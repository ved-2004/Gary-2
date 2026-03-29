"""
agents_llm.py

Drop-in replacement for agents.py — adds a working LLMAgent that calls
OpenAI to decide each action. Everything else (Agent, RandomAgent, Shopper,
GrabbableItem, AgentState, SimulationEngine) is unchanged from the original.

HOW TO USE IN main.py:
  1. Replace:  from agents import Agent, AgentState, GrabbableItem, RandomAgent
     With:     from agents_llm import Agent, AgentState, GrabbableItem, RandomAgent, LLMAgent

  2. In Engine.spawn_random_agents() (or add a new spawn_llm_agents()):
       self.random_agents = [
           LLMAgent(entrance.x, entrance.y,
                    name=agent_name,
                    profile=customer_profile_dict,
                    buying_list=["Whole Milk 1 gal", "Bananas lb", ...])
           for ...
       ]

  3. Set OPENAI_API_KEY in your environment before running main.py.

The LLM is called synchronously (blocking) because the pyray game loop is
single-threaded. Each agent gets one LLM call per step tick — the game loop
already controls tick rate via request_action().
"""

from dataclasses import asdict, dataclass, field
import json
import os
import random
import threading
from typing import Optional, Protocol

import pyray as pr

# ── Optional: load .env if python-dotenv is installed ─────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ── Re-export everything the original agents.py exported ──────────────────────

@dataclass(frozen=True)
class GrabbableItem:
    product_id: str
    product_name: str
    product_type: str
    company: str
    selling_price: float
    procurement_cost: float
    discount_percent: float
    margin_percent: float
    shelf_x: int
    shelf_y: int


@dataclass(frozen=True)
class AgentState:
    allowed_actions: list
    grabbable_items: list
    can_checkout: bool


class SimulationEngine(Protocol):
    def try_move_agent(self, agent: "Agent", dx: int, dy: int) -> bool: ...
    def try_grab_item(self, agent: "Agent", item: GrabbableItem) -> bool: ...
    def try_remove_item(self, agent: "Agent", item: GrabbableItem) -> bool: ...
    def try_checkout(self, agent: "Agent") -> bool: ...


@dataclass
class Agent:
    x: int
    y: int
    name: str = ""
    inventory: list = field(default_factory=list)
    checked_out_items: list = field(default_factory=list)

    def _move(self, engine: SimulationEngine, dx: int, dy: int) -> bool:
        return engine.try_move_agent(self, dx, dy)

    def move_left(self, engine: SimulationEngine) -> bool:
        return self._move(engine, -1, 0)

    def move_right(self, engine: SimulationEngine) -> bool:
        return self._move(engine, 1, 0)

    def move_up(self, engine: SimulationEngine) -> bool:
        return self._move(engine, 0, -1)

    def move_down(self, engine: SimulationEngine) -> bool:
        return self._move(engine, 0, 1)

    def grab(self, engine: SimulationEngine, item: GrabbableItem) -> bool:
        if engine.try_grab_item(self, item):
            self.inventory.append(item)
            return True
        return False

    def remove(self, engine: SimulationEngine) -> bool:
        if not self.inventory:
            return False
        item = self.inventory[0]
        if engine.try_remove_item(self, item):
            self.inventory.pop(0)
            return True
        return False

    def checkout(self, engine: SimulationEngine) -> bool:
        if not self.inventory:
            return False
        if engine.try_checkout(self):
            self.checked_out_items.extend(self.inventory)
            self.inventory.clear()
            return True
        return False

    def should_request_action(self) -> bool:
        return False

    def update(self, state: AgentState, engine: SimulationEngine) -> bool:
        return False


@dataclass
class Shopper(Agent):
    def should_request_action(self) -> bool:
        return any(
            pr.is_key_pressed(key)
            for key in (pr.KEY_A, pr.KEY_D, pr.KEY_W, pr.KEY_S,
                        pr.KEY_E, pr.KEY_Q, pr.KEY_C)
        )

    def update(self, state: AgentState, engine: SimulationEngine) -> bool:
        allowed_actions = set(state.allowed_actions)
        if pr.is_key_pressed(pr.KEY_A) and "move_left" in allowed_actions:
            return self.move_left(engine)
        if pr.is_key_pressed(pr.KEY_D) and "move_right" in allowed_actions:
            return self.move_right(engine)
        if pr.is_key_pressed(pr.KEY_W) and "move_up" in allowed_actions:
            return self.move_up(engine)
        if pr.is_key_pressed(pr.KEY_S) and "move_down" in allowed_actions:
            return self.move_down(engine)
        if pr.is_key_pressed(pr.KEY_E) and "grab" in allowed_actions and state.grabbable_items:
            return self.grab(engine, state.grabbable_items[0])
        if pr.is_key_pressed(pr.KEY_Q) and "remove" in allowed_actions:
            return self.remove(engine)
        if pr.is_key_pressed(pr.KEY_C) and "checkout" in allowed_actions:
            return self.checkout(engine)
        return False


@dataclass
class RandomAgent(Agent):
    pending_action_count: int = 0

    def request_action(self) -> None:
        self.pending_action_count += 1

    def should_request_action(self) -> bool:
        return self.pending_action_count > 0

    def update(self, state: AgentState, engine: SimulationEngine) -> bool:
        if self.pending_action_count > 0:
            self.pending_action_count -= 1
        possible_actions = list(state.allowed_actions)
        if not possible_actions:
            return False
        action = random.choice(possible_actions)
        if action == "move_left":   return self.move_left(engine)
        if action == "move_right":  return self.move_right(engine)
        if action == "move_up":     return self.move_up(engine)
        if action == "move_down":   return self.move_down(engine)
        if action == "grab" and state.grabbable_items:
            return self.grab(engine, random.choice(state.grabbable_items))
        if action == "remove":      return self.remove(engine)
        if action == "checkout":    return self.checkout(engine)
        return False


# ── LLM integration ────────────────────────────────────────────────────────────

_openai_client = None

def _get_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI()   # reads OPENAI_API_KEY from env
    return _openai_client


SYSTEM_PROMPT = """You are a grocery shopper navigating a store grid.

You will receive your current state as JSON and must respond with ONLY a JSON
object containing a single "action" key. No explanation, no markdown.

Valid actions: move_left, move_right, move_up, move_down, grab, remove, checkout

Rules:
- Only choose actions listed in allowed_actions.
- grab: pick up an item from an adjacent shelf. Only valid if grabbable_items is non-empty.
- checkout: only valid if can_checkout is true and you have inventory.
- remove: drops the first item from your inventory (use to discard unwanted items).
- Move toward shelves that have items on your buying list.
- Once your buying list is complete and you have inventory, navigate toward checkout.
- Impulse buy: if you see nearby items that match your interests, consider grabbing them.

Response format (exactly):
{"action": "move_right"}"""


def _build_user_message(agent: "LLMAgent", state: AgentState) -> str:
    bought = [i.product_name for i in agent.checked_out_items]
    in_cart = [i.product_name for i in agent.inventory]
    still_needed = [i for i in agent.buying_list if i not in bought and i not in in_cart]

    payload = {
        "agent": {
            "name": agent.name,
            "position": {"x": agent.x, "y": agent.y},
            "inventory": [asdict(i) for i in agent.inventory],
            "checked_out": [asdict(i) for i in agent.checked_out_items],
        },
        "buying_list": {
            "still_needed": still_needed,
            "in_cart": in_cart,
            "purchased": bought,
        },
        "profile": agent.profile,
        "state": {
            "allowed_actions": state.allowed_actions,
            "can_checkout": state.can_checkout,
            "grabbable_items": [asdict(i) for i in state.grabbable_items],
        },
        "step": agent.step_count,
    }
    return json.dumps(payload)


def _call_llm(agent: "LLMAgent", state: AgentState) -> Optional[str]:
    """
    Calls OpenAI synchronously and returns the action string, or None on failure.
    Runs in a background thread so the game loop doesn't freeze while waiting.
    """
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": _build_user_message(agent, state)},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
            max_tokens=50,
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        action = parsed.get("action", "")
        if action in state.allowed_actions:
            return action
        # If LLM returned invalid action, fall back to random valid one
        return random.choice(state.allowed_actions) if state.allowed_actions else None
    except Exception as e:
        print(f"[LLMAgent:{agent.name}] LLM error: {e}")
        return random.choice(state.allowed_actions) if state.allowed_actions else None


def _execute_action(
    action: str,
    agent: "LLMAgent",
    state: AgentState,
    engine: SimulationEngine,
) -> bool:
    if action == "move_left":   return agent.move_left(engine)
    if action == "move_right":  return agent.move_right(engine)
    if action == "move_up":     return agent.move_up(engine)
    if action == "move_down":   return agent.move_down(engine)
    if action == "grab" and state.grabbable_items:
        # Prefer items on the buying list, otherwise first available
        target = next(
            (i for i in state.grabbable_items
             if i.product_name in agent.buying_list),
            state.grabbable_items[0],
        )
        return agent.grab(engine, target)
    if action == "remove":      return agent.remove(engine)
    if action == "checkout":    return agent.checkout(engine)
    return False


@dataclass
class LLMAgent(Agent):
    """
    An agent whose decisions come from an LLM.

    The game loop calls request_action() each tick. The LLM call runs in a
    background thread so the UI stays responsive. When the result is ready,
    the next tick executes it.

    Args:
        profile: dict from customer_profiles.csv (name, income_bracket, etc.)
        buying_list: list of product_name strings this agent wants to buy
    """
    profile: dict = field(default_factory=dict)
    buying_list: list = field(default_factory=list)

    # Internal state
    pending_action_count: int = field(default=0, repr=False)
    step_count: int = field(default=0, repr=False)
    _pending_action: Optional[str] = field(default=None, repr=False)
    _thinking: bool = field(default=False, repr=False)

    def request_action(self) -> None:
        self.pending_action_count += 1

    def should_request_action(self) -> bool:
        return self.pending_action_count > 0

    def update(self, state: AgentState, engine: SimulationEngine) -> bool:
        if self.pending_action_count > 0:
            self.pending_action_count -= 1

        self.step_count += 1

        # If a previous async LLM call has returned an action, execute it
        if self._pending_action is not None:
            action = self._pending_action
            self._pending_action = None
            return _execute_action(action, self, state, engine)

        # If we're already waiting for LLM, skip this tick (don't double-call)
        if self._thinking:
            return False

        # Fire LLM call in background thread
        self._thinking = True
        captured_state = state  # capture for thread closure

        def _thread():
            action = _call_llm(self, captured_state)
            self._pending_action = action
            self._thinking = False

        threading.Thread(target=_thread, daemon=True).start()
        return False