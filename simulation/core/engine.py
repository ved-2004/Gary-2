from dataclasses import asdict, dataclass, field
import random
from agents import (
    Agent,
    AgentState,
    CheckoutHint,
    CustomerProfile,
    GrabbableItem,
    LLMAgent,
    NearbyShelfInfo,
)
from core.config import SimulationConfig
from core.store import Product, Shelf, find_shelf_at_cell


@dataclass
class Engine:
    shelves: list[Shelf] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)
    active_agents: list[LLMAgent] = field(default_factory=list)
    pending_spawns: list[LLMAgent] = field(default_factory=list)
    purchased_items: list[GrabbableItem] = field(default_factory=list)
    completed_agents: list[Agent] = field(default_factory=list)
    simulation_results_saved: bool = False

    def is_blocked(self, x: int, y: int) -> bool:
        return any(
            shelf.x == x and shelf.y == y and shelf.type != "entrance"
            for shelf in self.shelves
        )

    def get_total_revenue(self) -> float:
        return sum(item.selling_price for item in self.purchased_items)

    def has_active_simulation(self) -> bool:
        return bool(self.active_agents or self.pending_spawns or self.completed_agents)

    def should_save_results(self) -> bool:
        return (
            not self.active_agents
            and not self.pending_spawns
            and bool(self.completed_agents)
            and not self.simulation_results_saved
        )

    def find_entrances(self) -> list[Shelf]:
        return [shelf for shelf in self.shelves if shelf.type == "entrance"]

    def find_checkouts(self) -> list[Shelf]:
        return [shelf for shelf in self.shelves if shelf.type == "checkout"]

    def get_walkable_adjacent_positions(self, x: int, y: int) -> list[tuple[int, int]]:
        positions: list[tuple[int, int]] = []
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            next_x = x + dx
            next_y = y + dy
            if not self.is_blocked(next_x, next_y):
                positions.append((next_x, next_y))
        return positions

    def is_entrance_position(self, x: int, y: int) -> bool:
        shelf = find_shelf_at_cell(self.shelves, Shelf(x, y))
        return shelf is not None and shelf.type == "entrance"

    def get_adjacent_non_entrance_shelf_count(self, x: int, y: int) -> int:
        count = 0
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            shelf = find_shelf_at_cell(self.shelves, Shelf(x + dx, y + dy))
            if shelf is not None and shelf.type != "entrance":
                count += 1
        return count

    def pick_spawn_position(self, entrance: Shelf) -> tuple[int, int]:
        all_candidates = self.get_walkable_adjacent_positions(entrance.x, entrance.y)
        candidates = [
            (x, y)
            for x, y in all_candidates
            if not self.is_entrance_position(x, y)
        ]
        if not candidates:
            candidates = all_candidates
        if not candidates:
            return entrance.x, entrance.y

        best_score = max(
            self.get_adjacent_non_entrance_shelf_count(x, y)
            for x, y in candidates
        )
        best_candidates = [
            (x, y)
            for x, y in candidates
            if self.get_adjacent_non_entrance_shelf_count(x, y) == best_score
        ]
        return self.rng.choice(best_candidates)

    def get_stocked_product_names(self) -> set[str]:
        names: set[str] = set()
        for shelf in self.shelves:
            for product in shelf.products:
                names.add(product.product_name)
        return names

    def reset_simulation(self) -> None:
        for agent in self.active_agents + self.pending_spawns:
            if agent.request_future is not None:
                agent.request_future.cancel()
                agent.request_future = None
        self.purchased_items = []
        self.completed_agents = []
        self.simulation_results_saved = False
        self.active_agents = []
        self.pending_spawns = []

    def spawn_llm_agents(
        self,
        profiles: list[CustomerProfile],
        config: SimulationConfig,
        start_time: float,
        sprite_names: list[str] | None = None,
    ) -> list[LLMAgent]:
        entrances = self.find_entrances()
        self.reset_simulation()
        if not entrances:
            return []
        if config.agent_count > len(profiles):
            raise ValueError(
                f"Requested {config.agent_count} agents but only {len(profiles)} "
                "customer profiles are available."
            )

        stocked_names = self.get_stocked_product_names()
        spawned_agents: list[LLMAgent] = []
        selected_profiles = self.rng.sample(profiles, k=config.agent_count)
        for profile in selected_profiles:
            entrance = self.rng.choice(entrances)
            spawn_x, spawn_y = self.pick_spawn_position(entrance)
            spawn_at = start_time
            if config.spawn_delay_window_seconds > 0:
                spawn_at += self.rng.uniform(0, config.spawn_delay_window_seconds)

            all_targets = profile.get_target_products()
            available_targets = [t for t in all_targets if t in stocked_names]
            unavailable_targets = [t for t in all_targets if t not in stocked_names]

            agent = LLMAgent(
                x=spawn_x,
                y=spawn_y,
                name=profile.name,
                sprite_name=(
                    self.rng.choice(sprite_names)
                    if sprite_names
                    else ""
                ),
                customer_profile=profile,
                shopping_targets=available_targets,
                unavailable_targets=unavailable_targets,
                max_iterations=config.max_iterations_per_agent,
                spawn_at=spawn_at,
                next_action_at=spawn_at,
            )
            if spawn_at <= start_time:
                self.active_agents.append(agent)
            else:
                self.pending_spawns.append(agent)
            spawned_agents.append(agent)

        self.pending_spawns.sort(key=lambda agent: agent.spawn_at)
        return spawned_agents

    def activate_due_agents(self, now: float) -> list[LLMAgent]:
        activated: list[LLMAgent] = []
        remaining: list[LLMAgent] = []
        for agent in self.pending_spawns:
            if agent.spawn_at <= now:
                self.active_agents.append(agent)
                activated.append(agent)
            else:
                remaining.append(agent)
        self.pending_spawns = remaining
        return activated

    def count_in_flight_requests(self) -> int:
        return sum(
            1 for agent in self.active_agents if agent.request_future is not None
        )

    def get_nearest_checkout_hint(self, agent: Agent) -> CheckoutHint | None:
        checkouts = self.find_checkouts()
        if not checkouts:
            return None

        nearest_checkout = min(
            checkouts,
            key=lambda shelf: abs(shelf.x - agent.x) + abs(shelf.y - agent.y),
        )
        return CheckoutHint(
            target_x=nearest_checkout.x,
            target_y=nearest_checkout.y,
            delta_x=nearest_checkout.x - agent.x,
            delta_y=nearest_checkout.y - agent.y,
            manhattan_distance=(
                abs(nearest_checkout.x - agent.x) + abs(nearest_checkout.y - agent.y)
            ),
        )

    def retire_agent(self, agent: LLMAgent, reason: str) -> None:
        if agent.request_future is not None:
            agent.request_future.cancel()
            agent.request_future = None
        if agent in self.active_agents:
            self.active_agents.remove(agent)
        if agent in self.pending_spawns:
            self.pending_spawns.remove(agent)
        agent.completion_reason = reason
        if agent not in self.completed_agents:
            self.completed_agents.append(agent)

    def try_move_agent(self, agent: Agent, dx: int, dy: int) -> bool:
        target_x = agent.x + dx
        target_y = agent.y + dy
        if self.is_blocked(target_x, target_y):
            return False

        agent.x = target_x
        agent.y = target_y
        return True

    def get_grabbable_items(self, agent: Agent) -> list[GrabbableItem]:
        grabbable_items: list[GrabbableItem] = []
        adjacent_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in adjacent_offsets:
            shelf = find_shelf_at_cell(
                self.shelves,
                Shelf(agent.x + dx, agent.y + dy),
            )
            if shelf is None:
                continue

            for product in shelf.products:
                grabbable_items.append(
                    GrabbableItem(
                        product_id=product.id,
                        product_name=product.product_name,
                        product_type=product.product_type,
                        company=product.company,
                        selling_price=product.selling_price,
                        procurement_cost=product.procurement_cost,
                        discount_percent=product.discount_percent,
                        margin_percent=product.margin_percent,
                        shelf_x=shelf.x,
                        shelf_y=shelf.y,
                    )
                )

        return grabbable_items

    def can_checkout(self, agent: Agent) -> bool:
        adjacent_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in adjacent_offsets:
            shelf = find_shelf_at_cell(
                self.shelves,
                Shelf(agent.x + dx, agent.y + dy),
            )
            if shelf is not None and shelf.type == "checkout":
                return True
        return False

    def get_nearby_shelves(
        self, agent: Agent, radius: int = 6,
    ) -> list[NearbyShelfInfo]:
        results: list[NearbyShelfInfo] = []
        for shelf in self.shelves:
            dist = abs(shelf.x - agent.x) + abs(shelf.y - agent.y)
            if dist < 1 or dist > radius:
                continue
            product_names = tuple(p.product_name for p in shelf.products)
            if not product_names and shelf.type == "shelf":
                continue
            results.append(
                NearbyShelfInfo(
                    shelf_x=shelf.x,
                    shelf_y=shelf.y,
                    shelf_type=shelf.type,
                    manhattan_distance=dist,
                    product_names=product_names,
                )
            )
        results.sort(key=lambda s: s.manhattan_distance)
        return results

    def get_agent_state(self, agent: Agent) -> AgentState:
        allowed_actions: list[str] = []
        if not self.is_blocked(agent.x - 1, agent.y):
            allowed_actions.append("move_left")
        if not self.is_blocked(agent.x + 1, agent.y):
            allowed_actions.append("move_right")
        if not self.is_blocked(agent.x, agent.y - 1):
            allowed_actions.append("move_up")
        if not self.is_blocked(agent.x, agent.y + 1):
            allowed_actions.append("move_down")

        grabbable_items = self.get_grabbable_items(agent)
        if grabbable_items:
            allowed_actions.append("grab")
        if agent.inventory:
            allowed_actions.append("remove")
        if agent.inventory and self.can_checkout(agent):
            allowed_actions.append("checkout")

        return AgentState(
            allowed_actions,
            grabbable_items,
            self.can_checkout(agent),
            self.get_nearest_checkout_hint(agent),
            self.get_nearby_shelves(agent),
        )

    def try_grab_item(self, agent: Agent, item: GrabbableItem) -> bool:
        if any(i.product_id == item.product_id for i in agent.inventory):
            return False

        shelf = find_shelf_at_cell(self.shelves, Shelf(item.shelf_x, item.shelf_y))
        if shelf is None:
            return False

        for product in shelf.products:
            if product.id == item.product_id:
                return True

        return False

    def try_remove_item(self, agent: Agent, item: GrabbableItem) -> bool:
        return bool(agent.inventory)

    def try_checkout(self, agent: Agent) -> bool:
        if not agent.inventory or not self.can_checkout(agent):
            return False

        self.purchased_items.extend(agent.inventory)
        if agent in self.active_agents:
            self.active_agents.remove(agent)
        if isinstance(agent, LLMAgent):
            agent.completion_reason = "checked_out"
        self.completed_agents.append(agent)
        return True

    def build_results_payload(self) -> dict[str, object]:
        def build_agent_result(agent: Agent, state: str) -> dict[str, object]:
            purchased_items = [asdict(item) for item in agent.checked_out_items]
            agent_payload: dict[str, object] = {
                "name": agent.name,
                "state": state,
                "current_position": {"x": agent.x, "y": agent.y},
                "items_purchased": purchased_items,
                "spend": sum(item.selling_price for item in agent.checked_out_items),
                "inventory": [asdict(item) for item in agent.inventory],
            }
            if isinstance(agent, LLMAgent):
                agent_payload.update(
                    {
                        "customer_id": agent.customer_profile.customer_id,
                        "completion_reason": agent.completion_reason,
                        "iteration_count": agent.iteration_count,
                        "max_iterations": agent.max_iterations,
                        "unique_positions_visited": agent.get_unique_positions_visited(),
                        "shopping_targets": agent.shopping_targets,
                        "unavailable_targets": agent.unavailable_targets,
                        "remaining_targets": agent.get_remaining_targets(),
                        "failure_count": agent.failure_count,
                        "successful_action_count": agent.successful_action_count,
                        "last_error": agent.last_error,
                    }
                )
            return agent_payload

        agent_results = [
            build_agent_result(
                agent,
                (
                    agent.completion_reason
                    if isinstance(agent, LLMAgent)
                    else "completed"
                ),
            )
            for agent in self.completed_agents
        ]
        agent_results.extend(
            build_agent_result(agent, "active") for agent in self.active_agents
        )
        agent_results.extend(
            build_agent_result(agent, "pending_spawn")
            for agent in self.pending_spawns
        )

        return {
            "agents": agent_results,
            "total_revenue": self.get_total_revenue(),
        }
