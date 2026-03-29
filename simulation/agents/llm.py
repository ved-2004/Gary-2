import asyncio
from concurrent.futures import Future
from dataclasses import asdict, dataclass, field
import json
import threading
from typing import Any
from openai import AsyncOpenAI

from agents.base import Agent, SimulationEngine
from agents.customer import CustomerProfile
from agents.schema import ALLOWED_LLM_ACTIONS, ShopperActionResponse
from agents.state import (
    ActionRecord,
    AgentState,
    GrabbableItem,
    LLMAction,
    TrajectoryStep,
)


@dataclass(kw_only=True)
class LLMAgent(Agent):
    customer_profile: CustomerProfile
    shopping_targets: list[str]
    unavailable_targets: list[str] = field(default_factory=list)
    max_iterations: int = 50
    spawn_at: float = 0.0
    next_action_at: float = 0.0
    request_future: Future[LLMAction] | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    completion_reason: str = "active"
    last_error: str = ""
    failure_count: int = 0
    iteration_count: int = 0
    request_count: int = 0
    successful_action_count: int = 0
    recent_positions: list[tuple[int, int]] = field(default_factory=list)
    position_visit_counts: dict[tuple[int, int], int] = field(default_factory=dict)
    action_history: list[ActionRecord] = field(default_factory=list)
    trajectory_steps: list[TrajectoryStep] = field(
        default_factory=list, repr=False, compare=False,
    )
    trajectory_spawn_x: int = field(default=0, init=False, repr=False, compare=False)
    trajectory_spawn_y: int = field(default=0, init=False, repr=False, compare=False)

    MAX_ACTION_HISTORY: int = field(default=20, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.trajectory_spawn_x = self.x
        self.trajectory_spawn_y = self.y
        self.record_position()

    def get_owned_product_names(self) -> set[str]:
        owned = {item.product_name for item in self.inventory}
        owned.update(item.product_name for item in self.checked_out_items)
        return owned

    def get_remaining_targets(self) -> list[str]:
        owned = self.get_owned_product_names()
        return [target for target in self.shopping_targets if target not in owned]

    def get_remaining_iterations(self) -> int:
        return max(0, self.max_iterations - self.iteration_count)

    def get_unique_positions_visited(self) -> int:
        return len(self.position_visit_counts)

    def get_current_position_visits(self) -> int:
        return self.position_visit_counts.get((self.x, self.y), 0)

    def record_position(self) -> None:
        position = (self.x, self.y)
        self.position_visit_counts[position] = (
            self.position_visit_counts.get(position, 0) + 1
        )
        self.recent_positions.append(position)
        if len(self.recent_positions) > 20:
            self.recent_positions.pop(0)

    def get_adjacent_move_visit_counts(self, state: AgentState) -> dict[str, int]:
        visit_counts: dict[str, int] = {}
        move_offsets = {
            "move_left": (-1, 0),
            "move_right": (1, 0),
            "move_up": (0, -1),
            "move_down": (0, 1),
        }
        allowed_actions = set(state.allowed_actions)
        for action, (dx, dy) in move_offsets.items():
            if action not in allowed_actions:
                continue
            visit_counts[action] = self.position_visit_counts.get(
                (self.x + dx, self.y + dy),
                0,
            )
        return visit_counts

    def choose_less_visited_move(self, state: AgentState) -> str | None:
        move_visit_counts = self.get_adjacent_move_visit_counts(state)
        if not move_visit_counts:
            return None
        min_visits = min(move_visit_counts.values())
        best_actions = [
            action
            for action, visit_count in move_visit_counts.items()
            if visit_count == min_visits
        ]
        return sorted(best_actions)[0]

    def should_navigate_to_checkout(self) -> bool:
        if not self.inventory:
            return False
        if not self.get_remaining_targets():
            return True
        remaining_ratio = self.get_remaining_iterations() / max(self.max_iterations, 1)
        return remaining_ratio < 0.30

    def get_checkout_direction_move(self, state: AgentState) -> str | None:
        if state.nearest_checkout is None:
            return None
        allowed = set(state.allowed_actions)
        dx = state.nearest_checkout.delta_x
        dy = state.nearest_checkout.delta_y
        candidates: list[str] = []
        if dx > 0 and "move_right" in allowed:
            candidates.append("move_right")
        elif dx < 0 and "move_left" in allowed:
            candidates.append("move_left")
        if dy > 0 and "move_down" in allowed:
            candidates.append("move_down")
        elif dy < 0 and "move_up" in allowed:
            candidates.append("move_up")
        if candidates:
            return min(
                candidates,
                key=lambda a: self.position_visit_counts.get(
                    (
                        self.x + {"move_left": -1, "move_right": 1}.get(a, 0),
                        self.y + {"move_up": -1, "move_down": 1}.get(a, 0),
                    ),
                    0,
                ),
            )
        return None

    def _get_owned_product_ids(self) -> set[str]:
        ids = {item.product_id for item in self.inventory}
        ids.update(item.product_id for item in self.checked_out_items)
        return ids

    def adjust_llm_action(self, decision: LLMAction, state: AgentState) -> LLMAction:
        owned_ids = self._get_owned_product_ids()

        if self.inventory and state.can_checkout and self.get_remaining_iterations() <= 15:
            return LLMAction(action="checkout")

        remaining = set(self.get_remaining_targets())
        for item in state.grabbable_items:
            if item.product_name in remaining and item.product_id not in owned_ids:
                return LLMAction(action="grab", product_id=item.product_id)

        if decision.action == "grab" and decision.product_id:
            if decision.product_id in owned_ids:
                best_move = self.choose_less_visited_move(state)
                if best_move is not None:
                    return LLMAction(action=best_move)

        if self.should_navigate_to_checkout():
            if "checkout" in state.allowed_actions:
                return LLMAction(action="checkout")
            checkout_move = self.get_checkout_direction_move(state)
            if checkout_move is not None:
                return LLMAction(action=checkout_move)
            best_move = self.choose_less_visited_move(state)
            if best_move is not None:
                return LLMAction(action=best_move)

        move_visit_counts = self.get_adjacent_move_visit_counts(state)
        if not move_visit_counts:
            return decision

        if (
            not state.grabbable_items
            and decision.action in {"remove", "checkout"}
            and "checkout" not in state.allowed_actions
        ):
            best_move = self.choose_less_visited_move(state)
            if best_move is not None:
                return LLMAction(action=best_move)

        if (
            decision.action in move_visit_counts
            and not self.inventory
            and self.get_remaining_targets()
        ):
            selected_visits = move_visit_counts[decision.action]
            minimum_visits = min(move_visit_counts.values())
            if selected_visits > minimum_visits and not state.grabbable_items:
                best_move = self.choose_less_visited_move(state)
                if best_move is not None:
                    return LLMAction(action=best_move)

        return decision

    def build_system_prompt(self) -> str:
        behavioral = self.customer_profile.build_behavioral_directives()
        sections: list[str] = [
            self.customer_profile.build_persona_summary(),
            "",
        ]
        if behavioral:
            sections.append("YOUR SHOPPING PERSONALITY:")
            sections.append(behavioral)
            sections.append("")

        sections.extend([
            "You are shopping inside a 2D grocery simulation.",
            (
                "Return exactly one JSON object with three fields: reasoning, "
                "action, and product_id."
            ),
            (
                "reasoning: a single sentence describing your immediate plan "
                "(e.g. 'Heading right toward the produce shelf at (12,3) to "
                "grab avocado'). This sentence is stored and shown back to you "
                "on your next turn as your_last_plan, so write it for your "
                "future self."
            ),
            "Choose only one allowed action from the provided state.",
            (
                "If you choose grab, set product_id to a visible grabbable "
                "item's product_id. For all other actions, set product_id to null."
            ),
            "",
            "PLANNING:",
            (
                "- your_last_plan shows what you said you would do last turn. "
                "Follow through on it unless the situation has changed."
            ),
            (
                "- action_history shows your recent actions with their plan "
                "sentences. Use this to maintain a coherent multi-step route "
                "instead of re-deciding from scratch each turn."
            ),
            (
                "- If your last plan failed or you are stuck (oscillating "
                "between the same 2-3 positions), explicitly change your plan "
                "in reasoning and pick a new direction."
            ),
            "",
            "STRATEGY:",
            (
                "1. Grab any grabbable item where matches_target is true "
                "immediately -- this is always your highest priority."
            ),
            (
                "2. Impulse and treats (matches_target is false): you MAY grab items "
                "not on your list when they plausibly fit your shopping personality "
                "(e.g. organic snack if you prefer organic, a splurge if you have "
                "high spending power, something on sale if you are budget-conscious, "
                "a comfort food if that matches your profile). Explain the impulse in "
                "reasoning in one short clause. Do not grab random unrelated products."
            ),
            (
                "3. Keep impulse buying reasonable: skip extras when checkout_urgency "
                "is 'critical' or when you are almost out of iterations, unless you "
                "are already next to checkout with your list complete."
            ),
            (
                "4. Not all products may be stocked. shopping_plan.targets lists "
                "items actually on shelves. Items under unavailable_in_store "
                "are NOT stocked -- do not search for them."
            ),
            (
                "5. If checkout is in allowed_actions and you have items, choose "
                "checkout immediately."
            ),
            (
                "6. If you have items in your inventory and no remaining_targets, "
                "navigate straight to checkout using nearest_checkout.delta "
                "(positive delta.x = move right, positive delta.y = move down)."
            ),
            (
                "7. When remaining_iterations is below 30% and you hold items, "
                "head to checkout -- do NOT keep exploring."
            ),
            (
                "8. If checkout_urgency is 'high' or 'critical', drop everything "
                "and navigate to checkout."
            ),
            (
                "9. Prefer moves toward unvisited tiles (lowest value in "
                "adjacent_move_visit_counts). Avoid revisiting high-count tiles."
            ),
            "",
            "AWARENESS (use these to plan your route):",
            (
                "- nearby_shelves shows shelves within 6 tiles. Entries with "
                "has_target: true carry products you still need. Move toward "
                "those shelves first."
            ),
            (
                "- Each grabbable item has matches_target: true means it is on your "
                "remaining list. false means not on the list -- you may still grab "
                "it as an impulse buy if it fits your personality (see strategy 2)."
            ),
            (
                "- If a nearby shelf of type 'checkout' is visible and you have "
                "items, navigate toward it."
            ),
            "Do not invent products, actions, or coordinates.",
        ])
        return "\n".join(sections)

    def _compute_checkout_urgency(self) -> str:
        remaining = self.get_remaining_iterations()
        ratio = remaining / max(self.max_iterations, 1)
        if self.inventory:
            if ratio <= 0.10:
                return "critical"
            if ratio <= 0.30:
                return "high"
            if ratio <= 0.50:
                return "medium"
        else:
            if ratio <= 0.10:
                return "high"
            if ratio <= 0.30:
                return "medium"
        return "low"

    def _compute_navigation_hint(self, state: AgentState) -> str | None:
        if state.nearest_checkout is None:
            return None
        if not self.inventory:
            return None
        if state.can_checkout:
            return "You are adjacent to checkout. Use checkout now."
        dx = state.nearest_checkout.delta_x
        dy = state.nearest_checkout.delta_y
        parts: list[str] = []
        if dx > 0:
            parts.append("right")
        elif dx < 0:
            parts.append("left")
        if dy > 0:
            parts.append("down")
        elif dy < 0:
            parts.append("up")
        if parts:
            return "Move " + " and ".join(parts) + " to approach checkout."
        return None

    def build_state_snapshot(self, state: AgentState) -> str:
        remaining_targets = self.get_remaining_targets()
        remaining_set = set(remaining_targets)
        owned_ids = self._get_owned_product_ids()
        checkout_urgency = self._compute_checkout_urgency()
        navigation_hint = self._compute_navigation_hint(state)

        def serialize_item(item: GrabbableItem) -> dict[str, Any]:
            return {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_type": item.product_type,
                "company": item.company,
                "selling_price": item.selling_price,
                "discount_percent": item.discount_percent,
                "shelf": {"x": item.shelf_x, "y": item.shelf_y},
            }

        def serialize_grabbable(item: GrabbableItem) -> dict[str, Any]:
            data = serialize_item(item)
            data["matches_target"] = item.product_name in remaining_set
            return data

        filtered_grabbable = [
            item for item in state.grabbable_items
            if item.product_id not in owned_ids
        ]

        nearby_shelves_data: list[dict[str, Any]] = []
        for ns in state.nearby_shelves:
            has_target = any(p in remaining_set for p in ns.product_names)
            entry: dict[str, Any] = {
                "position": {"x": ns.shelf_x, "y": ns.shelf_y},
                "type": ns.shelf_type,
                "distance": ns.manhattan_distance,
            }
            if has_target:
                entry["has_target"] = True
            if ns.product_names:
                entry["products"] = list(ns.product_names)
            nearby_shelves_data.append(entry)

        history_data: list[dict[str, Any]] = []
        last_plan = ""
        for record in self.action_history:
            entry: dict[str, Any] = {
                "action": record.action,
                "ok": record.success,
                "pos": {"x": record.position_x, "y": record.position_y},
                "detail": record.detail,
            }
            if record.plan:
                entry["plan"] = record.plan
                last_plan = record.plan
            history_data.append(entry)

        payload: dict[str, Any] = {
            "agent": {
                "customer_id": self.customer_profile.customer_id,
                "name": self.customer_profile.name,
                "position": {"x": self.x, "y": self.y},
                "inventory": [serialize_item(item) for item in self.inventory],
                "checked_out_items": [
                    serialize_item(item) for item in self.checked_out_items
                ],
            },
            "exploration": {
                "iterations_used": self.iteration_count,
                "max_iterations": self.max_iterations,
                "remaining_iterations": self.get_remaining_iterations(),
                "checkout_urgency": checkout_urgency,
                "unique_positions_visited": self.get_unique_positions_visited(),
                "current_position_visits": self.get_current_position_visits(),
                "recent_positions": [
                    {"x": x, "y": y} for x, y in self.recent_positions
                ],
                "adjacent_move_visit_counts": self.get_adjacent_move_visit_counts(state),
            },
            "shopping_plan": {
                "targets": self.shopping_targets,
                "remaining_targets": remaining_targets,
                "unavailable_in_store": self.unavailable_targets,
            },
            "state": {
                "allowed_actions": state.allowed_actions,
                "can_checkout": state.can_checkout,
                "nearest_checkout": (
                    {
                        "target": {
                            "x": state.nearest_checkout.target_x,
                            "y": state.nearest_checkout.target_y,
                        },
                        "delta": {
                            "x": state.nearest_checkout.delta_x,
                            "y": state.nearest_checkout.delta_y,
                        },
                        "manhattan_distance": state.nearest_checkout.manhattan_distance,
                    }
                    if state.nearest_checkout is not None
                    else None
                ),
                "grabbable_items": [
                    serialize_grabbable(item) for item in filtered_grabbable
                ],
                "nearby_shelves": nearby_shelves_data,
            },
        }
        if last_plan:
            payload["your_last_plan"] = last_plan
        if navigation_hint is not None:
            payload["navigation_hint"] = navigation_hint
        if history_data:
            payload["action_history"] = history_data
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))

    def _record_action(
        self,
        action: str,
        success: bool,
        product_id: str | None,
        reasoning: str = "",
    ) -> None:
        if action == "grab" and product_id and success:
            detail = f"grabbed {product_id}"
        elif action == "checkout" and success:
            detail = f"checked out {len(self.checked_out_items)} item(s)"
        elif action.startswith("move_") and success:
            detail = f"moved to ({self.x},{self.y})"
        elif not success:
            detail = "failed"
        else:
            detail = "ok"
        self.action_history.append(
            ActionRecord(
                action=action,
                success=success,
                position_x=self.x,
                position_y=self.y,
                detail=detail,
                plan=reasoning,
            )
        )
        if len(self.action_history) > self.MAX_ACTION_HISTORY:
            self.action_history = self.action_history[-self.MAX_ACTION_HISTORY:]

    def apply_llm_action(
        self,
        decision: LLMAction,
        state: AgentState,
        engine: SimulationEngine,
    ) -> bool:
        pos_before_x, pos_before_y = self.x, self.y
        normalized_decision = self.adjust_llm_action(decision, state)
        self.iteration_count += 1
        applied = self.perform_action(
            normalized_decision.action,
            state,
            engine,
            product_id=normalized_decision.product_id,
        )
        self._record_action(
            normalized_decision.action,
            applied,
            normalized_decision.product_id,
            reasoning=decision.reasoning,
        )
        self.trajectory_steps.append(TrajectoryStep(
            iteration=self.iteration_count,
            position_before_x=pos_before_x,
            position_before_y=pos_before_y,
            raw_action=decision.action,
            raw_product_id=decision.product_id,
            raw_reasoning=decision.reasoning,
            adjusted_action=normalized_decision.action,
            adjusted_product_id=normalized_decision.product_id,
            success=applied,
            position_after_x=self.x,
            position_after_y=self.y,
            inventory_after=[asdict(i) for i in self.inventory],
            checked_out_items_after=[asdict(i) for i in self.checked_out_items],
        ))
        if applied:
            self.successful_action_count += 1
            self.record_position()
            self.last_error = ""
        else:
            self.failure_count += 1
            self.last_error = (
                f"Rejected action '{normalized_decision.action}' for current state"
            )
        return applied


def parse_llm_action_payload(payload: dict[str, object]) -> LLMAction:
    action = payload.get("action")
    if not isinstance(action, str) or action not in ALLOWED_LLM_ACTIONS:
        raise ValueError("LLM action payload must include a valid action.")

    raw_product_id = payload.get("product_id")
    if raw_product_id is not None and not isinstance(raw_product_id, str):
        raise ValueError("LLM action payload product_id must be a string or null.")

    raw_reasoning = payload.get("reasoning", "")
    reasoning = raw_reasoning if isinstance(raw_reasoning, str) else ""

    return LLMAction(action=action, product_id=raw_product_id, reasoning=reasoning)


class AsyncOpenAIActionRunner:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        reasoning_effort: str | None,
        max_concurrency: int,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_concurrency = max_concurrency
        self.timeout_seconds = timeout_seconds
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client: AsyncOpenAI | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._ready = threading.Event()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="openai-action-runner",
            daemon=True,
        )
        self._thread.start()
        if not self._ready.wait(timeout=5):
            raise RuntimeError("Timed out starting the OpenAI action runner.")

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._client = AsyncOpenAI(api_key=self.api_key)
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        self._ready.set()
        self._loop.run_forever()
        self._loop.close()

    async def _request_action(
        self,
        *,
        system_prompt: str,
        state_snapshot: str,
        shopper_id: str,
    ) -> LLMAction:
        if self._client is None or self._semaphore is None:
            raise RuntimeError("OpenAI action runner is not ready.")

        async with self._semaphore:
            request_kwargs: dict[str, Any] = {
                "model": self.model,
                "instructions": system_prompt,
                "input": state_snapshot,
                "max_output_tokens": 150,
                "store": False,
                "text_format": ShopperActionResponse,
                "timeout": self.timeout_seconds,
                "truncation": "disabled",
                "user": shopper_id,
            }
            if self.reasoning_effort is not None:
                request_kwargs["reasoning"] = {"effort": self.reasoning_effort}

            response = await self._client.responses.parse(
                **request_kwargs,
            )

        if response.output_parsed is not None:
            return parse_llm_action_payload(response.output_parsed.model_dump())

        refusal_messages: list[str] = []
        for output_item in response.output:
            if getattr(output_item, "type", None) != "message":
                continue
            for content_item in getattr(output_item, "content", []):
                if getattr(content_item, "type", None) == "refusal":
                    refusal_messages.append(content_item.refusal)
                elif getattr(content_item, "type", None) == "output_text":
                    return parse_llm_action_payload(json.loads(content_item.text))

        if refusal_messages:
            raise ValueError("OpenAI refusal: " + " ".join(refusal_messages))
        response_status = getattr(response, "status", "unknown")
        output_types = [
            getattr(output_item, "type", "unknown") for output_item in response.output
        ]
        raise ValueError(
            f"OpenAI returned no parsed action. status={response_status}, "
            f"output_types={output_types}"
        )

    def submit(
        self,
        *,
        system_prompt: str,
        state_snapshot: str,
        shopper_id: str,
    ) -> Future[LLMAction]:
        if self._loop is None:
            raise RuntimeError("OpenAI action runner loop is unavailable.")
        coroutine = self._request_action(
            system_prompt=system_prompt,
            state_snapshot=state_snapshot,
            shopper_id=shopper_id,
        )
        return asyncio.run_coroutine_threadsafe(coroutine, self._loop)

    async def _shutdown(self) -> None:
        if self._client is not None:
            await self._client.close()

    def close(self) -> None:
        if self._loop is None:
            return

        try:
            shutdown_future = asyncio.run_coroutine_threadsafe(
                self._shutdown(),
                self._loop,
            )
            shutdown_future.result(timeout=5)
        except Exception:
            pass

        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
