from dataclasses import asdict, dataclass, field
import json
import random
from typing import Protocol

import pyray as pr


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
    allowed_actions: list[str]
    grabbable_items: list[GrabbableItem]
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
    inventory: list[GrabbableItem] = field(default_factory=list)
    checked_out_items: list[GrabbableItem] = field(default_factory=list)

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
            for key in (
                pr.KEY_A,
                pr.KEY_D,
                pr.KEY_W,
                pr.KEY_S,
                pr.KEY_E,
                pr.KEY_Q,
                pr.KEY_C,
            )
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
        if (
            pr.is_key_pressed(pr.KEY_E)
            and "grab" in allowed_actions
            and state.grabbable_items
        ):
            return self.grab(engine, state.grabbable_items[0])
        if (
            pr.is_key_pressed(pr.KEY_Q)
            and "remove" in allowed_actions
        ):
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
        if action == "move_left":
            return self.move_left(engine)
        if action == "move_right":
            return self.move_right(engine)
        if action == "move_up":
            return self.move_up(engine)
        if action == "move_down":
            return self.move_down(engine)
        if action == "grab" and state.grabbable_items:
            return self.grab(engine, random.choice(state.grabbable_items))
        if action == "remove":
            return self.remove(engine)
        if action == "checkout":
            return self.checkout(engine)
        return False


@dataclass
class LLMAgent(Agent):
    pending_action_count: int = 0

    def request_action(self) -> None:
        self.pending_action_count += 1

    def should_request_action(self) -> bool:
        return self.pending_action_count > 0

    def update(self, state: AgentState, engine: SimulationEngine) -> bool:
        if self.pending_action_count > 0:
            self.pending_action_count -= 1

        state_payload = {
            "agent": {
                "name": self.name,
                "position": {"x": self.x, "y": self.y},
                "inventory": [asdict(item) for item in self.inventory],
                "checked_out_items": [asdict(item) for item in self.checked_out_items],
            },
            "state": {
                "allowed_actions": state.allowed_actions,
                "can_checkout": state.can_checkout,
                "grabbable_items": [asdict(item) for item in state.grabbable_items],
            },
        }
        state_json = json.dumps(state_payload)

        # TODO: Call the LLM with the current state JSON and get back an action.
        # TODO: Validate and execute the returned action against the engine.
        _ = state_json
        return False
