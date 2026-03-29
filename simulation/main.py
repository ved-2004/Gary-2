import argparse
import csv
from dataclasses import asdict, dataclass, field
import json
import math
import os
from pathlib import Path
import random
import time

from plyer import filechooser
import pyray as pr
from agents import (
    Agent,
    AgentState,
    AsyncOpenAIActionRunner,
    CheckoutHint,
    CustomerNeed,
    CustomerProfile,
    GrabbableItem,
    LLMAction,
    LLMAgent,
    NearbyShelfInfo,
)

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
GRID_SIZE = 40
GRID_EXTENT = 4000
GRID_POINT_COLOR = pr.LIGHTGRAY
GRID_POINT_RADIUS = 3
BUTTON_WIDTH = 140
BUTTON_HEIGHT = 40
BUTTON_GAP = 16
BUTTON_TOP_MARGIN = 16
BUTTON_ROW_GAP = 12
BUTTON_TEXT_SIZE = 20
BUTTON_COLOR = pr.LIGHTGRAY
BUTTON_ACTIVE_COLOR = pr.SKYBLUE
BUTTON_HOVER_COLOR = pr.SKYBLUE
BUTTON_BORDER_COLOR = pr.DARKGRAY
BUTTON_TEXT_COLOR = pr.DARKGRAY
LOAD_BUTTON_WIDTH = 180
LAYOUT_BUTTON_WIDTH = 180
MODE_BUTTON_WIDTH = 160
PRODUCT_PANEL_WIDTH = 420
PRODUCT_PANEL_MARGIN = 20
PRODUCT_PANEL_PADDING = 24
PRODUCT_PANEL_LINE_HEIGHT = 30
PRODUCT_PANEL_HEADER_HEIGHT = 192
PRODUCT_SECTION_HEADER_HEIGHT = 34
PRODUCT_SECTION_GAP = 12
PRODUCT_ITEM_HEIGHT = 72
PRODUCT_ITEM_GAP = 10
PANEL_SECTION_GAP = 18
PANEL_TITLE_FONT_SIZE = 32
PANEL_NAME_FONT_SIZE = 28
PANEL_SECTION_TITLE_FONT_SIZE = 26
PANEL_BODY_FONT_SIZE = 24
PANEL_HINT_FONT_SIZE = 20
STATUS_PRIMARY_FONT_SIZE = 24
STATUS_SECONDARY_FONT_SIZE = 22
SHELF_TYPE_SHELF_COLOR = pr.BLUE
SHELF_TYPE_CHECKOUT_COLOR = pr.GREEN
SHELF_TYPE_ENTRANCE_COLOR = pr.MAGENTA
SHELF_PREVIEW_COLOR = pr.SKYBLUE
SHELF_HOVER_COLOR = pr.GOLD
SHELF_SELECTED_COLOR = pr.GOLD
SHELF_DELETE_PREVIEW_COLOR = pr.RED
SHELF_BORDER_COLOR = pr.DARKBLUE
CELL_HOVER_COLOR = pr.GOLD
SELECTION_COLOR = pr.DARKBLUE
PRODUCT_ITEM_HOVER_COLOR = pr.SKYBLUE
ORIGIN_MARKER_COLOR = pr.LIGHTGRAY
SHOPPER_COLOR = pr.BLACK
SHOPPER_SELECTED_COLOR = pr.RED
SHOPPER_RADIUS = 10
SHELF_PADDING = 4
MIN_ZOOM = 0.1
MAX_ZOOM = 8.0
MAX_LLM_AGENT_COUNT = 15
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_REASONING_EFFORT = "none"
DEFAULT_ACTION_COOLDOWN_SECONDS = 2.0
DEFAULT_SPAWN_DELAY_WINDOW_SECONDS = 0.0
DEFAULT_OPENAI_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_ITERATIONS_PER_AGENT = 100
SUPPORTED_REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh")
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
ROOT_ENV_PATH = ROOT_DIR / ".env"
CUSTOMER_PROFILES_PATH = DATA_DIR / "customer_profiles.csv"
SHOPPING_LIST_PATH = DATA_DIR / "shopping_list.csv"
RESULTS_PATH = Path(__file__).resolve().parent / "results.json"
JSON_FILE_FILTERS = [("JSON files", "*.json"), ("All files", "*.*")]


@dataclass(frozen=True)
class SimulationConfig:
    agent_count: int = MAX_LLM_AGENT_COUNT
    model: str = DEFAULT_MODEL
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT
    action_cooldown_seconds: float = DEFAULT_ACTION_COOLDOWN_SECONDS
    spawn_delay_window_seconds: float = DEFAULT_SPAWN_DELAY_WINDOW_SECONDS
    max_iterations_per_agent: int = DEFAULT_MAX_ITERATIONS_PER_AGENT
    max_concurrency: int = MAX_LLM_AGENT_COUNT
    seed: int | None = None


@dataclass
class Shelf:
    x: int
    y: int
    type: str = "shelf"
    products: list["Product"] = field(default_factory=list)


@dataclass(frozen=True)
class Product:
    id: str
    product_name: str
    product_type: str
    company: str
    selling_price: float
    procurement_cost: float
    discount_percent: float
    margin_percent: float


@dataclass
class ProductListView:
    scroll_offset: float = 0.0
    render_texture: object | None = None
    texture_width: int = 0
    texture_height: int = 0


@dataclass
class Engine:
    shelves: list["Shelf"] = field(default_factory=list)
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


def parse_agent_count(value: str) -> int:
    parsed_value = int(value)
    if parsed_value < 1 or parsed_value > MAX_LLM_AGENT_COUNT:
        raise argparse.ArgumentTypeError(
            f"Agent count must be between 1 and {MAX_LLM_AGENT_COUNT}."
        )
    return parsed_value


def parse_non_negative_float(value: str) -> float:
    parsed_value = float(value)
    if parsed_value < 0:
        raise argparse.ArgumentTypeError("Value must be non-negative.")
    return parsed_value


def parse_positive_int(value: str) -> int:
    parsed_value = int(value)
    if parsed_value < 1:
        raise argparse.ArgumentTypeError("Value must be at least 1.")
    return parsed_value


def validate_reasoning_effort(model: str, reasoning_effort: str | None) -> None:
    if reasoning_effort is None:
        return

    normalized_model = model.strip().lower()
    if normalized_model.startswith("gpt-5-mini"):
        raise argparse.ArgumentTypeError(
            "gpt-5-mini uses fixed medium reasoning and does not support "
            "--reasoning-effort overrides."
        )

    if normalized_model.startswith("gpt-5.4"):
        allowed = {"none", "low", "medium", "high", "xhigh"}
    elif normalized_model.startswith("gpt-5.1"):
        allowed = {"none", "low", "medium", "high"}
    elif normalized_model.startswith("gpt-5-pro"):
        allowed = {"high"}
    elif normalized_model == "gpt-5" or normalized_model.startswith("gpt-5-"):
        allowed = {"minimal", "low", "medium", "high"}
    else:
        return

    if reasoning_effort not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise argparse.ArgumentTypeError(
            f"{model} supports reasoning efforts: {allowed_text}."
        )


def parse_cli_args() -> SimulationConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--agent-count",
        type=parse_agent_count,
        default=MAX_LLM_AGENT_COUNT,
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=SUPPORTED_REASONING_EFFORTS,
        default=DEFAULT_REASONING_EFFORT,
    )
    parser.add_argument(
        "--action-cooldown-seconds",
        type=parse_non_negative_float,
        default=DEFAULT_ACTION_COOLDOWN_SECONDS,
    )
    parser.add_argument(
        "--spawn-delay-window-seconds",
        type=parse_non_negative_float,
        default=DEFAULT_SPAWN_DELAY_WINDOW_SECONDS,
    )
    parser.add_argument(
        "--max-iterations-per-agent",
        type=parse_positive_int,
        default=DEFAULT_MAX_ITERATIONS_PER_AGENT,
    )
    parser.add_argument(
        "--max-concurrency",
        type=parse_positive_int,
        default=MAX_LLM_AGENT_COUNT,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
    )
    args = parser.parse_args()
    try:
        validate_reasoning_effort(args.model, args.reasoning_effort)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    max_concurrency = min(args.max_concurrency, args.agent_count, MAX_LLM_AGENT_COUNT)
    return SimulationConfig(
        agent_count=args.agent_count,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        action_cooldown_seconds=args.action_cooldown_seconds,
        spawn_delay_window_seconds=args.spawn_delay_window_seconds,
        max_iterations_per_agent=args.max_iterations_per_agent,
        max_concurrency=max_concurrency,
        seed=args.seed,
    )


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        env_key = key.strip()
        env_value = value.strip().strip('"').strip("'")
        if env_key and env_key not in os.environ:
            os.environ[env_key] = env_value


def get_openai_api_key() -> str:
    load_env_file(ROOT_ENV_PATH)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            f"OPENAI_API_KEY is missing. Expected it in {ROOT_ENV_PATH} or the environment."
        )
    return api_key


def split_pipe_values(raw_value: str) -> tuple[str, ...]:
    return tuple(
        value.strip()
        for value in raw_value.split("|")
        if value.strip()
    )


def parse_csv_bool(raw_value: str) -> bool:
    return raw_value.strip().lower() in {"1", "true", "yes", "y"}


def load_customer_profiles(
    customer_profiles_path: Path = CUSTOMER_PROFILES_PATH,
    shopping_list_path: Path = SHOPPING_LIST_PATH,
) -> list[CustomerProfile]:
    with customer_profiles_path.open(newline="", encoding="utf-8") as customer_file:
        customer_rows = list(csv.DictReader(customer_file))
    with shopping_list_path.open(newline="", encoding="utf-8") as shopping_file:
        shopping_rows = list(csv.DictReader(shopping_file))

    shopping_by_customer: dict[str, tuple[str, tuple[CustomerNeed, ...]]] = {}
    for row in shopping_rows:
        customer_id = row["customer_id"].strip()
        shopping_needs: list[CustomerNeed] = []
        need_index = 1
        while f"need_{need_index}" in row:
            need_name = row.get(f"need_{need_index}", "").strip()
            need_type = row.get(f"need_{need_index}_product_type", "").strip()
            shopping_list = split_pipe_values(row.get(f"shopping_list_{need_index}", ""))
            if need_name:
                shopping_needs.append(
                    CustomerNeed(
                        name=need_name,
                        product_type=need_type,
                        shopping_list=shopping_list,
                    )
                )
            need_index += 1

        shopping_by_customer[customer_id] = (
            row.get("name", "").strip(),
            tuple(shopping_needs),
        )

    profiles: list[CustomerProfile] = []
    seen_customer_ids: set[str] = set()
    for row in customer_rows:
        customer_id = row["customer_id"].strip()
        customer_name = row["name"].strip()
        if customer_id not in shopping_by_customer:
            raise ValueError(
                f"Customer {customer_id} is missing from {shopping_list_path.name}."
            )

        shopping_name, shopping_needs = shopping_by_customer[customer_id]
        if shopping_name and shopping_name != customer_name:
            raise ValueError(
                f"Customer name mismatch for {customer_id}: "
                f"{customer_name!r} vs {shopping_name!r}."
            )

        profiles.append(
            CustomerProfile(
                customer_id=customer_id,
                name=customer_name,
                age=int(row["age"]),
                gender=row["gender"].strip(),
                income_bracket=row["income_bracket"].strip(),
                churned=parse_csv_bool(row["churned"]),
                marital_status=row["marital_status"].strip(),
                number_of_children=int(row["number_of_children"]),
                education_level=row["education_level"].strip(),
                occupation=row["occupation"].strip(),
                race=row["race"].strip(),
                disability=parse_csv_bool(row["disability"]),
                height_cm=int(row["height"]),
                customer_needs=split_pipe_values(row["customer_needs"]),
                purchased_alcohol_before=parse_csv_bool(
                    row["purchased_alcohol_before"]
                ),
                fitness_level=row["fitness_level"].strip(),
                organic_preference=parse_csv_bool(row["organic_preference"]),
                total_historical_purchase=float(row["total_historical_purchase"]),
                avg_purchase_value=float(row["avg_purchase_value"]),
                shopping_needs=shopping_needs,
            )
        )
        seen_customer_ids.add(customer_id)

    extra_customer_ids = sorted(set(shopping_by_customer) - seen_customer_ids)
    if extra_customer_ids:
        raise ValueError(
            "Shopping list rows are missing customer profile rows for: "
            + ", ".join(extra_customer_ids)
        )

    profiles.sort(key=lambda profile: profile.customer_id)
    return profiles


def draw_grid(grid_size: int, extent: int) -> None:
    for x in range(-extent, extent + 1, grid_size):
        for y in range(-extent, extent + 1, grid_size):
            pr.draw_circle(x, y, GRID_POINT_RADIUS, GRID_POINT_COLOR)


def get_cell_at_position(position: pr.Vector2, grid_size: int) -> Shelf:
    return Shelf(
        math.floor(position.x / grid_size),
        math.floor(position.y / grid_size),
    )


def build_shelves(start: Shelf, end: Shelf) -> list[Shelf]:
    min_x = min(start.x, end.x)
    max_x = max(start.x, end.x)
    min_y = min(start.y, end.y)
    max_y = max(start.y, end.y)
    shelves: list[Shelf] = []

    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            shelves.append(Shelf(x, y))

    return shelves


def find_shelf_at_cell(shelves: list[Shelf], cell: Shelf) -> Shelf | None:
    for shelf in shelves:
        if shelf.x == cell.x and shelf.y == cell.y:
            return shelf
    return None


def add_shelves(shelves: list[Shelf], new_shelves: list[Shelf]) -> None:
    existing_positions = {(shelf.x, shelf.y) for shelf in shelves}
    for shelf in new_shelves:
        if (shelf.x, shelf.y) not in existing_positions:
            shelves.append(shelf)
            existing_positions.add((shelf.x, shelf.y))


def remove_shelves(shelves: list[Shelf], shelves_to_remove: list[Shelf]) -> list[Shelf]:
    positions_to_remove = {(shelf.x, shelf.y) for shelf in shelves_to_remove}
    return [
        shelf for shelf in shelves if (shelf.x, shelf.y) not in positions_to_remove
    ]


def get_shelf_type_color(shelf_type: str) -> pr.Color:
    if shelf_type == "checkout":
        return SHELF_TYPE_CHECKOUT_COLOR
    if shelf_type == "entrance":
        return SHELF_TYPE_ENTRANCE_COLOR
    return SHELF_TYPE_SHELF_COLOR


def draw_shelf(shelf: Shelf, color: pr.Color) -> None:
    x = shelf.x * GRID_SIZE + SHELF_PADDING
    y = shelf.y * GRID_SIZE + SHELF_PADDING
    size = GRID_SIZE - SHELF_PADDING * 2
    pr.draw_rectangle(x, y, size, size, color)


def draw_shelves(
    shelves: list[Shelf],
    hovered_shelf: Shelf | None = None,
    selected_shelf: Shelf | None = None,
) -> None:
    for shelf in shelves:
        color = get_shelf_type_color(shelf.type)
        draw_shelf(shelf, color)
        if shelf == selected_shelf:
            pr.draw_rectangle(
                shelf.x * GRID_SIZE + SHELF_PADDING,
                shelf.y * GRID_SIZE + SHELF_PADDING,
                GRID_SIZE - SHELF_PADDING * 2,
                GRID_SIZE - SHELF_PADDING * 2,
                SHELF_SELECTED_COLOR,
            )
        elif shelf == hovered_shelf:
            pr.draw_rectangle(
                shelf.x * GRID_SIZE + SHELF_PADDING,
                shelf.y * GRID_SIZE + SHELF_PADDING,
                GRID_SIZE - SHELF_PADDING * 2,
                GRID_SIZE - SHELF_PADDING * 2,
                SHELF_HOVER_COLOR,
            )
        pr.draw_rectangle_lines(
            shelf.x * GRID_SIZE + SHELF_PADDING,
            shelf.y * GRID_SIZE + SHELF_PADDING,
            GRID_SIZE - SHELF_PADDING * 2,
            GRID_SIZE - SHELF_PADDING * 2,
            SHELF_BORDER_COLOR,
        )


def draw_cell_outline(cell: Shelf, color: pr.Color) -> None:
    x = cell.x * GRID_SIZE
    y = cell.y * GRID_SIZE
    pr.draw_rectangle_lines(x, y, GRID_SIZE, GRID_SIZE, color)


def draw_selection_outline(start: Shelf, end: Shelf) -> None:
    min_x = min(start.x, end.x) * GRID_SIZE
    max_x = (max(start.x, end.x) + 1) * GRID_SIZE
    min_y = min(start.y, end.y) * GRID_SIZE
    max_y = (max(start.y, end.y) + 1) * GRID_SIZE
    pr.draw_line(min_x, min_y, max_x, min_y, SELECTION_COLOR)
    pr.draw_line(max_x, min_y, max_x, max_y, SELECTION_COLOR)
    pr.draw_line(max_x, max_y, min_x, max_y, SELECTION_COLOR)
    pr.draw_line(min_x, max_y, min_x, min_y, SELECTION_COLOR)


def draw_origin_marker() -> None:
    pr.draw_rectangle(0, 0, GRID_SIZE, GRID_SIZE, ORIGIN_MARKER_COLOR)


def draw_agent(agent: Agent) -> None:
    center_x = agent.x * GRID_SIZE + GRID_SIZE / 2
    center_y = agent.y * GRID_SIZE + GRID_SIZE / 2
    pr.draw_circle(int(center_x), int(center_y), SHOPPER_RADIUS, SHOPPER_COLOR)


def draw_agent_selection(agent: Agent) -> None:
    center_x = agent.x * GRID_SIZE + GRID_SIZE / 2
    center_y = agent.y * GRID_SIZE + GRID_SIZE / 2
    pr.draw_circle_lines(
        int(center_x),
        int(center_y),
        SHOPPER_RADIUS + 4,
        SHOPPER_SELECTED_COLOR,
    )


def find_agent_at_world_position(
    agents: list[Agent],
    world_position: pr.Vector2,
) -> Agent | None:
    selected_agent: Agent | None = None
    selected_distance_sq: float | None = None
    for agent in agents:
        center_x = agent.x * GRID_SIZE + GRID_SIZE / 2
        center_y = agent.y * GRID_SIZE + GRID_SIZE / 2
        delta_x = world_position.x - center_x
        delta_y = world_position.y - center_y
        distance_sq = delta_x * delta_x + delta_y * delta_y
        if distance_sq > SHOPPER_RADIUS * SHOPPER_RADIUS:
            continue
        if selected_distance_sq is None or distance_sq < selected_distance_sq:
            selected_agent = agent
            selected_distance_sq = distance_sq
    return selected_agent


def get_shelf_type_button_rects(panel_rect: pr.Rectangle) -> dict[str, pr.Rectangle]:
    button_y = panel_rect.y + 84
    button_width = (panel_rect.width - PRODUCT_PANEL_PADDING * 2 - BUTTON_GAP * 2) / 3
    start_x = panel_rect.x + PRODUCT_PANEL_PADDING
    return {
        "shelf": pr.Rectangle(start_x, button_y, button_width, BUTTON_HEIGHT),
        "checkout": pr.Rectangle(
            start_x + button_width + BUTTON_GAP,
            button_y,
            button_width,
            BUTTON_HEIGHT,
        ),
        "entrance": pr.Rectangle(
            start_x + (button_width + BUTTON_GAP) * 2,
            button_y,
            button_width,
            BUTTON_HEIGHT,
        ),
    }


def get_available_products(all_products: list[Product], shelf: Shelf) -> list[Product]:
    assigned_product_ids = {product.id for product in shelf.products}
    return [product for product in all_products if product.id not in assigned_product_ids]


def get_product_panel_rect(screen_width: int, screen_height: int) -> pr.Rectangle:
    panel_y = get_ui_row_y(2) + 24
    return pr.Rectangle(
        screen_width - PRODUCT_PANEL_WIDTH - PRODUCT_PANEL_MARGIN,
        panel_y,
        PRODUCT_PANEL_WIDTH,
        max(220, screen_height - panel_y - PRODUCT_PANEL_MARGIN),
    )


def get_local_product_item_rects(
    width: float,
    products: list[Product],
) -> list[tuple[Product, pr.Rectangle]]:
    item_rects: list[tuple[Product, pr.Rectangle]] = []
    current_y = 0.0

    for product in products:
        item_rects.append(
            (
                product,
                pr.Rectangle(
                    0,
                    current_y,
                    width,
                    PRODUCT_ITEM_HEIGHT,
                ),
            )
        )
        current_y += PRODUCT_ITEM_HEIGHT + PRODUCT_ITEM_GAP

    return item_rects


def get_product_panel_sections(
    panel_rect: pr.Rectangle,
) -> tuple[pr.Rectangle, pr.Rectangle]:
    content_top = panel_rect.y + PRODUCT_PANEL_HEADER_HEIGHT
    content_height = panel_rect.height - PRODUCT_PANEL_HEADER_HEIGHT - PRODUCT_PANEL_PADDING
    half_height = (content_height - PRODUCT_SECTION_GAP) / 2
    section_width = panel_rect.width - PRODUCT_PANEL_PADDING * 2

    top_list_rect = pr.Rectangle(
        panel_rect.x + PRODUCT_PANEL_PADDING,
        content_top + PRODUCT_SECTION_HEADER_HEIGHT,
        section_width,
        half_height - PRODUCT_SECTION_HEADER_HEIGHT,
    )
    bottom_list_rect = pr.Rectangle(
        panel_rect.x + PRODUCT_PANEL_PADDING,
        content_top + half_height + PRODUCT_SECTION_GAP + PRODUCT_SECTION_HEADER_HEIGHT,
        section_width,
        half_height - PRODUCT_SECTION_HEADER_HEIGHT,
    )
    return top_list_rect, bottom_list_rect


def format_currency(amount: float, currency_code: str) -> str:
    if currency_code == "USD":
        return f"${amount:.2f}"
    return f"{currency_code} {amount:.2f}"


def product_to_dict(product: Product) -> dict[str, str | float]:
    return {
        "id": product.id,
        "product_name": product.product_name,
        "product_type": product.product_type,
        "company": product.company,
        "selling_price": product.selling_price,
        "procurement_cost": product.procurement_cost,
        "discount_percent": product.discount_percent,
        "margin_percent": product.margin_percent,
    }


def parse_product(raw_product: dict, index: int) -> Product:
    return Product(
        id=str(raw_product["id"]),
        product_name=str(raw_product["product_name"]),
        product_type=str(raw_product["product_type"]),
        company=str(raw_product["company"]),
        selling_price=float(raw_product["selling_price"]),
        procurement_cost=float(raw_product["procurement_cost"]),
        discount_percent=float(raw_product["discount_percent"]),
        margin_percent=float(raw_product["margin_percent"]),
    )


def shelf_to_dict(shelf: Shelf) -> dict:
    return {
        "world_grid_position": {"x": shelf.x, "y": shelf.y},
        "type": shelf.type,
        "product_ids": [product.id for product in shelf.products],
    }


def get_product_list_content_height(products: list[Product]) -> int:
    if not products:
        return PRODUCT_ITEM_HEIGHT
    return len(products) * PRODUCT_ITEM_HEIGHT + (len(products) - 1) * PRODUCT_ITEM_GAP


def clamp_scroll_offset(
    scroll_offset: float,
    viewport_height: float,
    content_height: float,
) -> float:
    max_scroll = max(0.0, content_height - viewport_height)
    return max(0.0, min(scroll_offset, max_scroll))


def ensure_list_view_texture(
    list_view: ProductListView,
    width: int,
    height: int,
) -> None:
    if width <= 0 or height <= 0:
        return

    if (
        list_view.render_texture is None
        or list_view.texture_width != width
        or list_view.texture_height != height
    ):
        if list_view.render_texture is not None:
            pr.unload_render_texture(list_view.render_texture)
        list_view.render_texture = pr.load_render_texture(width, height)
        list_view.texture_width = width
        list_view.texture_height = height


def unload_list_view_texture(list_view: ProductListView) -> None:
    if list_view.render_texture is not None:
        pr.unload_render_texture(list_view.render_texture)
        list_view.render_texture = None
        list_view.texture_width = 0
        list_view.texture_height = 0


def draw_product_item(
    rect: pr.Rectangle,
    product: Product,
    is_hovered: bool,
    currency_code: str,
) -> None:
    fill_color = PRODUCT_ITEM_HOVER_COLOR if is_hovered else pr.fade(BUTTON_COLOR, 0.75)
    pr.draw_rectangle_rec(rect, fill_color)
    pr.draw_rectangle_lines(
        int(rect.x),
        int(rect.y),
        int(rect.width),
        int(rect.height),
        BUTTON_BORDER_COLOR,
    )
    pr.draw_text(
        product.product_name,
        int(rect.x + 10),
        int(rect.y + 10),
        PANEL_BODY_FONT_SIZE,
        BUTTON_TEXT_COLOR,
    )
    pr.draw_text(
        (
            f"{product.product_type} | {product.company} | "
            f"{format_currency(product.selling_price, currency_code)} | "
            f"{product.margin_percent:.0f}% margin"
        ),
        int(rect.x + 10),
        int(rect.y + 40),
        PANEL_HINT_FONT_SIZE,
        pr.GRAY,
    )


def get_hovered_product_in_list(
    viewport_rect: pr.Rectangle,
    products: list[Product],
    scroll_offset: float,
    mouse_position: pr.Vector2,
) -> Product | None:
    if not pr.check_collision_point_rec(mouse_position, viewport_rect):
        return None

    local_x = mouse_position.x - viewport_rect.x
    local_y = scroll_offset + (mouse_position.y - viewport_rect.y)
    point = pr.Vector2(local_x, local_y)
    for product, rect in get_local_product_item_rects(viewport_rect.width, products):
        if pr.check_collision_point_rec(point, rect):
            return product
    return None


def draw_product_list_view(
    viewport_rect: pr.Rectangle,
    list_view: ProductListView,
    products: list[Product],
    empty_message: str,
    hovered_product: Product | None,
    currency_code: str,
) -> None:
    content_height = get_product_list_content_height(products)
    ensure_list_view_texture(
        list_view,
        max(1, int(math.ceil(viewport_rect.width))),
        max(1, int(math.ceil(viewport_rect.height))),
    )
    list_view.scroll_offset = clamp_scroll_offset(
        list_view.scroll_offset,
        viewport_rect.height,
        content_height,
    )

    if list_view.render_texture is None:
        return

    pr.draw_rectangle_rec(viewport_rect, pr.fade(BUTTON_COLOR, 0.15))
    pr.begin_texture_mode(list_view.render_texture)
    pr.clear_background(pr.BLANK)

    if not products:
        pr.draw_text(
            empty_message,
            0,
            8,
            PANEL_HINT_FONT_SIZE,
            pr.GRAY,
        )
    else:
        for product, rect in get_local_product_item_rects(viewport_rect.width, products):
            draw_rect = pr.Rectangle(
                rect.x,
                rect.y - list_view.scroll_offset,
                rect.width,
                rect.height,
            )
            if draw_rect.y + draw_rect.height < 0 or draw_rect.y > viewport_rect.height:
                continue
            draw_product_item(
                draw_rect,
                product,
                product == hovered_product,
                currency_code,
            )

    pr.end_texture_mode()

    source_rect = pr.Rectangle(
        0,
        0,
        viewport_rect.width,
        -viewport_rect.height,
    )
    pr.draw_texture_rec(
        list_view.render_texture.texture,
        source_rect,
        pr.Vector2(viewport_rect.x, viewport_rect.y),
        pr.WHITE,
    )
    pr.draw_rectangle_lines(
        int(viewport_rect.x),
        int(viewport_rect.y),
        int(viewport_rect.width),
        int(viewport_rect.height),
        BUTTON_BORDER_COLOR,
    )


def draw_product_panel(
    panel_rect: pr.Rectangle,
    shelf: Shelf,
    all_products: list[Product],
    mouse_position: pr.Vector2,
    is_editable: bool,
    currency_code: str,
    assigned_list_view: ProductListView,
    available_list_view: ProductListView,
) -> None:
    pr.draw_rectangle_rec(panel_rect, pr.fade(pr.RAYWHITE, 0.96))
    pr.draw_rectangle_lines(
        int(panel_rect.x),
        int(panel_rect.y),
        int(panel_rect.width),
        int(panel_rect.height),
        BUTTON_BORDER_COLOR,
    )

    text_x = int(panel_rect.x + PRODUCT_PANEL_PADDING)
    header_y = int(panel_rect.y + PRODUCT_PANEL_PADDING)
    pr.draw_text(
        "Shelf Products",
        text_x,
        header_y,
        PANEL_TITLE_FONT_SIZE,
        BUTTON_TEXT_COLOR,
    )
    pr.draw_text(
        f"Shelf ({shelf.x}, {shelf.y})",
        text_x,
        header_y + 42,
        PANEL_BODY_FONT_SIZE,
        pr.GRAY,
    )
    pr.draw_text(
        f"Type: {shelf.type.title()}",
        text_x,
        header_y + 72,
        PANEL_BODY_FONT_SIZE,
        pr.GRAY,
    )
    if is_editable:
        pr.draw_text(
            "Click type buttons or move products",
            text_x,
            header_y + 144,
            PANEL_HINT_FONT_SIZE,
            pr.GRAY,
        )
    else:
        pr.draw_text(
            "Hover preview",
            text_x,
            header_y + 144,
            PANEL_HINT_FONT_SIZE,
            pr.GRAY,
        )

    type_button_rects = get_shelf_type_button_rects(panel_rect)
    for shelf_type, button_rect in type_button_rects.items():
        draw_button(
            button_rect,
            shelf_type.title(),
            is_active=shelf.type == shelf_type,
            is_hovered=pr.check_collision_point_rec(mouse_position, button_rect),
        )

    top_list_rect, bottom_list_rect = get_product_panel_sections(panel_rect)
    top_section = pr.Rectangle(
        top_list_rect.x,
        top_list_rect.y - PRODUCT_SECTION_HEADER_HEIGHT,
        top_list_rect.width,
        top_list_rect.height + PRODUCT_SECTION_HEADER_HEIGHT,
    )
    bottom_section = pr.Rectangle(
        bottom_list_rect.x,
        bottom_list_rect.y - PRODUCT_SECTION_HEADER_HEIGHT,
        bottom_list_rect.width,
        bottom_list_rect.height + PRODUCT_SECTION_HEADER_HEIGHT,
    )

    pr.draw_text(
        "In Shelf",
        int(top_section.x),
        int(top_section.y),
        PANEL_SECTION_TITLE_FONT_SIZE,
        BUTTON_TEXT_COLOR,
    )
    pr.draw_text(
        "All Products",
        int(bottom_section.x),
        int(bottom_section.y),
        PANEL_SECTION_TITLE_FONT_SIZE,
        BUTTON_TEXT_COLOR,
    )

    available_products = get_available_products(all_products, shelf)
    hovered_assigned_product = get_hovered_product_in_list(
        top_list_rect,
        shelf.products,
        assigned_list_view.scroll_offset,
        mouse_position,
    )
    hovered_available_product = get_hovered_product_in_list(
        bottom_list_rect,
        available_products,
        available_list_view.scroll_offset,
        mouse_position,
    )

    draw_product_list_view(
        top_list_rect,
        assigned_list_view,
        shelf.products,
        "Click a product below to add it" if is_editable else "No products assigned",
        hovered_assigned_product,
        currency_code,
    )
    draw_product_list_view(
        bottom_list_rect,
        available_list_view,
        available_products,
        "No available products",
        hovered_available_product,
        currency_code,
    )


def get_agent_last_reasoning(agent: LLMAgent) -> str:
    for record in reversed(agent.action_history):
        if record.plan:
            return record.plan
    return ""


def wrap_panel_text(text: str, max_width: int, font_size: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}"
        if pr.measure_text(candidate, font_size) <= max_width:
            current_line = candidate
            continue
        lines.append(current_line)
        current_line = word
    lines.append(current_line)
    return lines


def draw_agent_panel(
    panel_rect: pr.Rectangle,
    agent: LLMAgent,
    currency_code: str,
) -> None:
    pr.draw_rectangle_rec(panel_rect, pr.fade(pr.RAYWHITE, 0.96))
    pr.draw_rectangle_lines(
        int(panel_rect.x),
        int(panel_rect.y),
        int(panel_rect.width),
        int(panel_rect.height),
        BUTTON_BORDER_COLOR,
    )

    text_x = int(panel_rect.x + PRODUCT_PANEL_PADDING)
    text_width = int(panel_rect.width - PRODUCT_PANEL_PADDING * 2)
    header_y = int(panel_rect.y + PRODUCT_PANEL_PADDING)
    line_y = header_y

    pr.draw_text(
        "Shopper Details",
        text_x,
        line_y,
        PANEL_TITLE_FONT_SIZE,
        BUTTON_TEXT_COLOR,
    )
    line_y += 42
    pr.draw_text(agent.name, text_x, line_y, PANEL_NAME_FONT_SIZE, BUTTON_TEXT_COLOR)
    line_y += 36
    pr.draw_text(
        f"Position: ({agent.x}, {agent.y})",
        text_x,
        line_y,
        PANEL_BODY_FONT_SIZE,
        pr.GRAY,
    )
    line_y += 30
    pr.draw_text(
        f"Inventory: {len(agent.inventory)} item(s)",
        text_x,
        line_y,
        PANEL_BODY_FONT_SIZE,
        pr.GRAY,
    )
    line_y += 30

    if agent.request_future is not None:
        status_text = "Status: waiting for next model response"
    else:
        status_text = f"Status: {agent.completion_reason.replace('_', ' ')}"
    pr.draw_text(status_text, text_x, line_y, PANEL_BODY_FONT_SIZE, pr.GRAY)
    line_y += 40

    pr.draw_text(
        "Inventory",
        text_x,
        line_y,
        PANEL_SECTION_TITLE_FONT_SIZE,
        BUTTON_TEXT_COLOR,
    )
    line_y += 34
    if agent.inventory:
        for item in agent.inventory:
            inventory_line = (
                f"- {item.product_name} | {item.company} | "
                f"{format_currency(item.selling_price, currency_code)}"
            )
            for wrapped_line in wrap_panel_text(
                inventory_line,
                text_width,
                PANEL_BODY_FONT_SIZE,
            ):
                pr.draw_text(
                    wrapped_line,
                    text_x,
                    line_y,
                    PANEL_BODY_FONT_SIZE,
                    pr.GRAY,
                )
                line_y += PRODUCT_PANEL_LINE_HEIGHT
    else:
        pr.draw_text(
            "No items in inventory",
            text_x,
            line_y,
            PANEL_BODY_FONT_SIZE,
            pr.GRAY,
        )
        line_y += PRODUCT_PANEL_LINE_HEIGHT

    line_y += PANEL_SECTION_GAP
    pr.draw_text(
        "Last Reasoning",
        text_x,
        line_y,
        PANEL_SECTION_TITLE_FONT_SIZE,
        BUTTON_TEXT_COLOR,
    )
    line_y += 34
    reasoning = get_agent_last_reasoning(agent)
    if not reasoning:
        reasoning = "No reasoning recorded yet."
    for wrapped_line in wrap_panel_text(reasoning, text_width, PANEL_BODY_FONT_SIZE):
        pr.draw_text(
            wrapped_line,
            text_x,
            line_y,
            PANEL_BODY_FONT_SIZE,
            pr.GRAY,
        )
        line_y += PRODUCT_PANEL_LINE_HEIGHT


def choose_single_file(selection: list[str] | None) -> str:
    if not selection:
        return ""
    return str(selection[0])


def pick_products_file() -> str:
    selected_path = filechooser.open_file(
        path=str(Path.cwd()),
        title="Select products JSON",
        filters=JSON_FILE_FILTERS,
    )
    return choose_single_file(selected_path)


def pick_layout_load_file() -> str:
    selected_path = filechooser.open_file(
        path=str(Path.cwd()),
        title="Select layout JSON",
        filters=JSON_FILE_FILTERS,
    )
    return choose_single_file(selected_path)


def pick_layout_save_file() -> str:
    selected_path = filechooser.save_file(
        path=str(Path.cwd() / "layout.json"),
        title="Save layout JSON",
        filters=JSON_FILE_FILTERS,
    )
    return choose_single_file(selected_path)


def load_products_from_json(path: str) -> tuple[list[Product], str]:
    with Path(path).open(encoding="utf-8") as file:
        raw_catalog = json.load(file)

    if not isinstance(raw_catalog, dict):
        raise ValueError("Product JSON must contain a top-level object.")

    raw_products = raw_catalog.get("products")
    if not isinstance(raw_products, list):
        raise ValueError("Product JSON must contain a 'products' list.")

    currency_code = str(raw_catalog.get("currency", "USD"))

    products: list[Product] = []
    for index, raw_product in enumerate(raw_products, start=1):
        if not isinstance(raw_product, dict):
            raise ValueError(f"Product {index} must be an object.")

        products.append(parse_product(raw_product, index))

    return products, currency_code


def save_layout_to_json(
    path: str,
    shelves: list[Shelf],
    products: list[Product],
    currency_code: str,
) -> None:
    layout_data = {
        "currency": currency_code,
        "products": [product_to_dict(product) for product in products],
        "shelves": [shelf_to_dict(shelf) for shelf in shelves],
    }
    Path(path).write_text(json.dumps(layout_data, indent=2), encoding="utf-8")


def load_layout_from_json(path: str) -> tuple[list[Shelf], list[Product], str]:
    with Path(path).open(encoding="utf-8") as file:
        raw_layout = json.load(file)

    if not isinstance(raw_layout, dict):
        raise ValueError("Layout JSON must contain a top-level object.")

    raw_products = raw_layout.get("products")
    raw_shelves = raw_layout.get("shelves")
    if not isinstance(raw_products, list):
        raise ValueError("Layout JSON must contain a 'products' list.")
    if not isinstance(raw_shelves, list):
        raise ValueError("Layout JSON must contain a 'shelves' list.")

    currency_code = str(raw_layout.get("currency", "USD"))
    products: list[Product] = []
    for index, raw_product in enumerate(raw_products, start=1):
        if not isinstance(raw_product, dict):
            raise ValueError(f"Layout product {index} must be an object.")
        products.append(parse_product(raw_product, index))

    products_by_id = {product.id: product for product in products}
    shelves: list[Shelf] = []
    for index, raw_shelf in enumerate(raw_shelves, start=1):
        if not isinstance(raw_shelf, dict):
            raise ValueError(f"Layout shelf {index} must be an object.")

        raw_position = raw_shelf.get("world_grid_position")
        if not isinstance(raw_position, dict):
            raise ValueError(
                f"Layout shelf {index} must have a 'world_grid_position' object."
            )

        raw_product_ids = raw_shelf.get("product_ids", [])
        if not isinstance(raw_product_ids, list):
            raise ValueError(f"Layout shelf {index} must have a 'product_ids' list.")

        shelf_products: list[Product] = []
        for product_id in raw_product_ids:
            product_key = str(product_id)
            if product_key not in products_by_id:
                raise ValueError(
                    f"Layout shelf {index} references unknown product id '{product_key}'."
                )
            shelf_products.append(products_by_id[product_key])

        shelves.append(
            Shelf(
                int(raw_position["x"]),
                int(raw_position["y"]),
                str(raw_shelf.get("type", "shelf")),
                shelf_products,
            )
        )

    return shelves, products, currency_code


def start_simulation(
    engine: Engine,
    shopper_profiles: list[CustomerProfile],
    config: SimulationConfig,
    now: float,
) -> str:
    spawned_agents = engine.spawn_llm_agents(shopper_profiles, config, now)
    if not spawned_agents:
        return "Simulation requires at least one entrance shelf"

    if engine.pending_spawns:
        return (
            f"Spawned {len(spawned_agents)} LLM shoppers: "
            f"{len(engine.active_agents)} active, {len(engine.pending_spawns)} delayed"
        )
    return f"Spawned {len(spawned_agents)} LLM shoppers"


def submit_due_llm_requests(
    engine: Engine,
    action_runner: AsyncOpenAIActionRunner,
    config: SimulationConfig,
    now: float,
) -> str | None:
    latest_status: str | None = None
    for agent in list(engine.active_agents):
        if agent.request_future is not None or now < agent.next_action_at:
            continue

        if not agent.shopping_targets and not agent.inventory:
            engine.retire_agent(agent, "nothing_to_buy")
            latest_status = f"{agent.name} retired - no products available in store"
            continue

        state = engine.get_agent_state(agent)
        if agent.iteration_count >= agent.max_iterations:
            if "checkout" in state.allowed_actions:
                if agent.apply_llm_action(
                    decision=LLMAction(action="checkout"),
                    state=state,
                    engine=engine,
                ):
                    latest_status = f"{agent.name} checked out at iteration limit"
                continue

            engine.retire_agent(agent, "max_iterations_reached")
            latest_status = (
                f"{agent.name} exited after reaching {agent.max_iterations} iterations"
            )
            continue

        if (
            agent.inventory
            and state.can_checkout
            and agent.get_remaining_iterations() <= 10
        ):
            if agent.apply_llm_action(
                decision=LLMAction(action="checkout"),
                state=state,
                engine=engine,
            ):
                latest_status = f"{agent.name} checked out with low turns remaining"
            continue

        if not state.allowed_actions:
            agent.next_action_at = now + config.action_cooldown_seconds
            continue

        try:
            agent.request_future = action_runner.submit(
                system_prompt=agent.build_system_prompt(),
                state_snapshot=agent.build_state_snapshot(state),
                shopper_id=agent.customer_profile.customer_id,
            )
            agent.request_count += 1
            agent.last_error = ""
        except Exception as exc:
            agent.failure_count += 1
            agent.last_error = f"Failed to submit OpenAI request: {exc}"
            agent.next_action_at = now + config.action_cooldown_seconds
            latest_status = f"{agent.name}: {agent.last_error}"

    return latest_status


def resolve_completed_llm_requests(
    engine: Engine,
    config: SimulationConfig,
    now: float,
) -> str | None:
    latest_status: str | None = None
    for agent in list(engine.active_agents):
        future = agent.request_future
        if future is None or not future.done():
            continue

        agent.request_future = None
        agent.next_action_at = now + config.action_cooldown_seconds

        try:
            decision = future.result()
        except Exception as exc:
            agent.iteration_count += 1
            agent.failure_count += 1
            agent.last_error = f"OpenAI request failed: {exc}"
            latest_status = f"{agent.name}: {agent.last_error}"
            continue

        state = engine.get_agent_state(agent)
        applied = agent.apply_llm_action(decision, state, engine)
        if not applied:
            latest_status = f"{agent.name}: {agent.last_error}"
        elif agent not in engine.active_agents:
            latest_status = f"{agent.name} checked out"

    return latest_status


def get_mode_button_rects(screen_width: int) -> dict[str, pr.Rectangle]:
    total_width = MODE_BUTTON_WIDTH * 3 + BUTTON_GAP * 2
    start_x = (screen_width - total_width) / 2
    return {
        "layout": pr.Rectangle(start_x, get_ui_row_y(1), MODE_BUTTON_WIDTH, BUTTON_HEIGHT),
        "products": pr.Rectangle(
            start_x + MODE_BUTTON_WIDTH + BUTTON_GAP,
            get_ui_row_y(1),
            MODE_BUTTON_WIDTH,
            BUTTON_HEIGHT,
        ),
        "simulation": pr.Rectangle(
            start_x + (MODE_BUTTON_WIDTH + BUTTON_GAP) * 2,
            get_ui_row_y(1),
            MODE_BUTTON_WIDTH,
            BUTTON_HEIGHT,
        ),
    }


def get_ui_row_y(row_index: int) -> int:
    return BUTTON_TOP_MARGIN + row_index * (BUTTON_HEIGHT + BUTTON_ROW_GAP)


def get_status_text_y() -> int:
    return pr.get_screen_height() - 84


def get_top_action_button_rects(screen_width: int) -> dict[str, pr.Rectangle]:
    total_width = LOAD_BUTTON_WIDTH + LAYOUT_BUTTON_WIDTH * 2 + BUTTON_GAP * 2
    start_x = (screen_width - total_width) / 2
    return {
        "load_products": pr.Rectangle(
            start_x,
            get_ui_row_y(0),
            LOAD_BUTTON_WIDTH,
            BUTTON_HEIGHT,
        ),
        "save_layout": pr.Rectangle(
            start_x + LOAD_BUTTON_WIDTH + BUTTON_GAP,
            get_ui_row_y(0),
            LAYOUT_BUTTON_WIDTH,
            BUTTON_HEIGHT,
        ),
        "load_layout": pr.Rectangle(
            start_x + LOAD_BUTTON_WIDTH + BUTTON_GAP + LAYOUT_BUTTON_WIDTH + BUTTON_GAP,
            get_ui_row_y(0),
            LAYOUT_BUTTON_WIDTH,
            BUTTON_HEIGHT,
        ),
    }


def draw_button(
    button: pr.Rectangle,
    label: str,
    is_active: bool = False,
    is_hovered: bool = False,
) -> None:
    fill_color = BUTTON_ACTIVE_COLOR if is_active else BUTTON_COLOR
    if is_hovered and not is_active:
        fill_color = BUTTON_HOVER_COLOR
    pr.draw_rectangle_rec(button, fill_color)
    pr.draw_rectangle_lines(
        int(button.x),
        int(button.y),
        int(button.width),
        int(button.height),
        BUTTON_BORDER_COLOR,
    )
    text_width = pr.measure_text(label, BUTTON_TEXT_SIZE)
    text_x = int(button.x + (button.width - text_width) / 2)
    text_y = int(button.y + (button.height - BUTTON_TEXT_SIZE) / 2)
    pr.draw_text(label, text_x, text_y, BUTTON_TEXT_SIZE, BUTTON_TEXT_COLOR)


def main():
    simulation_config = parse_cli_args()
    shopper_profiles: list[CustomerProfile] = []
    simulation_boot_error = ""
    action_runner: AsyncOpenAIActionRunner | None = None

    try:
        shopper_profiles = load_customer_profiles()
        action_runner = AsyncOpenAIActionRunner(
            api_key=get_openai_api_key(),
            model=simulation_config.model,
            reasoning_effort=simulation_config.reasoning_effort,
            max_concurrency=simulation_config.max_concurrency,
            timeout_seconds=DEFAULT_OPENAI_TIMEOUT_SECONDS,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        simulation_boot_error = str(exc)

    pr.set_config_flags(pr.FLAG_WINDOW_RESIZABLE)
    pr.init_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Grid")
    pr.set_target_fps(60)
    camera = pr.Camera2D(
        pr.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2),
        pr.Vector2(0, 0),
        0.0,
        1.0,
    )
    shelves: list[Shelf] = []
    engine = Engine(
        shelves=shelves,
        rng=random.Random(simulation_config.seed),
    )
    products: list[Product] = []
    product_currency = "USD"
    status_message = "No products loaded"
    if shopper_profiles:
        status_message = (
            f"Loaded {len(shopper_profiles)} shopper profiles | model "
            f"{simulation_config.model} | reasoning "
            f"{simulation_config.reasoning_effort or 'model default'}"
        )
    if simulation_boot_error:
        status_message = f"Simulation unavailable: {simulation_boot_error}"
    selection_start: Shelf | None = None
    selection_end: Shelf | None = None
    selection_mode: str | None = None
    current_mode = "layout"
    selected_shelf: Shelf | None = None
    selected_agent_id: str | None = None
    assigned_list_view = ProductListView()
    available_list_view = ProductListView()
    active_panel_shelf_key: tuple[int, int] | None = None

    try:
        while not pr.window_should_close():
            screen_width = pr.get_screen_width()
            screen_height = pr.get_screen_height()
            mouse_position = pr.get_mouse_position()
            ctrl_down = pr.is_key_down(pr.KEY_LEFT_CONTROL) or pr.is_key_down(
                pr.KEY_RIGHT_CONTROL
            )
            ctrl_left_mouse_pressed = (
                ctrl_down and pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT)
            )
            ctrl_left_mouse_down = ctrl_down and pr.is_mouse_button_down(
                pr.MOUSE_BUTTON_LEFT
            )
            left_mouse_pressed = (
                pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT)
                and not ctrl_left_mouse_pressed
            )
            button_rects = get_mode_button_rects(screen_width)
            top_action_button_rects = get_top_action_button_rects(screen_width)
            panel_rect = get_product_panel_rect(screen_width, screen_height)
            top_list_rect, bottom_list_rect = get_product_panel_sections(panel_rect)
            clicked_button = None
            clicked_load_products = False
            clicked_save_layout = False
            clicked_load_layout = False

            for mode_name, button in button_rects.items():
                if (
                    left_mouse_pressed
                    and pr.check_collision_point_rec(mouse_position, button)
                ):
                    clicked_button = mode_name
                    break

            if (
                clicked_button is None
                and left_mouse_pressed
                and pr.check_collision_point_rec(
                    mouse_position, top_action_button_rects["load_products"]
                )
            ):
                clicked_load_products = True

            if (
                clicked_button is None
                and not clicked_load_products
                and left_mouse_pressed
                and pr.check_collision_point_rec(
                    mouse_position, top_action_button_rects["save_layout"]
                )
            ):
                clicked_save_layout = True

            if (
                clicked_button is None
                and not clicked_load_products
                and not clicked_save_layout
                and left_mouse_pressed
                and pr.check_collision_point_rec(
                    mouse_position, top_action_button_rects["load_layout"]
                )
            ):
                clicked_load_layout = True

            if clicked_button is not None:
                current_mode = clicked_button
                selection_start = None
                selection_end = None
                selection_mode = None
                if current_mode != "simulation":
                    selected_agent_id = None
                if current_mode == "simulation":
                    if simulation_boot_error or action_runner is None:
                        engine.reset_simulation()
                        status_message = (
                            "Cannot start simulation: "
                            f"{simulation_boot_error or 'OpenAI runner unavailable'}"
                        )
                    else:
                        try:
                            status_message = start_simulation(
                                engine,
                                shopper_profiles,
                                simulation_config,
                                time.monotonic(),
                            )
                        except ValueError as exc:
                            engine.reset_simulation()
                            status_message = f"Cannot start simulation: {exc}"
                else:
                    engine.reset_simulation()

            if clicked_load_products:
                try:
                    selected_path = pick_products_file()
                    if selected_path:
                        products, product_currency = load_products_from_json(selected_path)
                        status_message = (
                            f"Loaded {len(products)} products from "
                            f"{Path(selected_path).name}"
                        )
                    else:
                        status_message = "Product load canceled"
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    status_message = f"Failed to load products: {exc}"
                selection_start = None
                selection_end = None
                selection_mode = None

            if clicked_save_layout:
                try:
                    selected_path = pick_layout_save_file()
                    if selected_path:
                        save_layout_to_json(
                            selected_path,
                            shelves,
                            products,
                            product_currency,
                        )
                        status_message = (
                            f"Saved layout with {len(shelves)} shelves to "
                            f"{Path(selected_path).name}"
                        )
                    else:
                        status_message = "Layout save canceled"
                except (OSError, ValueError, TypeError) as exc:
                    status_message = f"Failed to save layout: {exc}"
                selection_start = None
                selection_end = None
                selection_mode = None

            if clicked_load_layout:
                try:
                    selected_path = pick_layout_load_file()
                    if selected_path:
                        shelves, products, product_currency = load_layout_from_json(
                            selected_path
                        )
                        engine.shelves = shelves
                        selected_shelf = None
                        selected_agent_id = None
                        active_panel_shelf_key = None
                        assigned_list_view.scroll_offset = 0.0
                        available_list_view.scroll_offset = 0.0
                        if current_mode == "simulation":
                            if simulation_boot_error or action_runner is None:
                                engine.reset_simulation()
                                status_message = (
                                    f"Loaded layout from {Path(selected_path).name} | "
                                    "Simulation unavailable"
                                )
                            else:
                                status_message = start_simulation(
                                    engine,
                                    shopper_profiles,
                                    simulation_config,
                                    time.monotonic(),
                                )
                        else:
                            engine.reset_simulation()
                            status_message = (
                                f"Loaded layout with {len(shelves)} shelves from "
                                f"{Path(selected_path).name}"
                            )
                    else:
                        status_message = "Layout load canceled"
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    status_message = f"Failed to load layout: {exc}"
                selection_start = None
                selection_end = None
                selection_mode = None

            if ctrl_down and selection_mode is not None:
                selection_start = None
                selection_end = None
                selection_mode = None

            mouse_wheel = pr.get_mouse_wheel_move()
            mouse_world_position = pr.get_screen_to_world_2d(mouse_position, camera)
            hovered_cell = get_cell_at_position(mouse_world_position, GRID_SIZE)
            hovered_shelf = find_shelf_at_cell(shelves, hovered_cell)
            clicked_agent = find_agent_at_world_position(
                engine.active_agents,
                mouse_world_position,
            )
            if selected_shelf is not None:
                selected_shelf = find_shelf_at_cell(shelves, selected_shelf)
            selected_agent = None
            if selected_agent_id is not None:
                selected_agent = next(
                    (
                        agent
                        for agent in engine.active_agents
                        if agent.customer_profile.customer_id == selected_agent_id
                    ),
                    None,
                )
                if selected_agent is None:
                    selected_agent_id = None
            if current_mode == "products":
                panel_shelf = (
                    selected_shelf if selected_shelf is not None else hovered_shelf
                )
            elif current_mode == "simulation":
                panel_shelf = hovered_shelf if selected_agent is None else None
            else:
                panel_shelf = None

            panel_shelf_key = None
            if panel_shelf is not None:
                panel_shelf_key = (panel_shelf.x, panel_shelf.y)
            if panel_shelf_key != active_panel_shelf_key:
                assigned_list_view.scroll_offset = 0.0
                available_list_view.scroll_offset = 0.0
                active_panel_shelf_key = panel_shelf_key

            if (
                current_mode in {"products", "simulation"}
                and panel_shelf is not None
                and mouse_wheel != 0
            ):
                if pr.check_collision_point_rec(mouse_position, top_list_rect):
                    assigned_list_view.scroll_offset -= mouse_wheel * 40
                    assigned_list_view.scroll_offset = clamp_scroll_offset(
                        assigned_list_view.scroll_offset,
                        top_list_rect.height,
                        get_product_list_content_height(panel_shelf.products),
                    )
                    mouse_wheel = 0
                elif pr.check_collision_point_rec(mouse_position, bottom_list_rect):
                    available_list_view.scroll_offset -= mouse_wheel * 40
                    available_list_view.scroll_offset = clamp_scroll_offset(
                        available_list_view.scroll_offset,
                        bottom_list_rect.height,
                        get_product_list_content_height(
                            get_available_products(products, panel_shelf)
                        ),
                    )
                    mouse_wheel = 0

            mouse_world_before_zoom = pr.get_screen_to_world_2d(mouse_position, camera)
            if mouse_wheel != 0:
                camera.offset = mouse_position
                camera.target = mouse_world_before_zoom
                camera.zoom = min(
                    MAX_ZOOM,
                    max(MIN_ZOOM, camera.zoom + mouse_wheel * 0.1),
                )

            if pr.is_mouse_button_down(pr.MOUSE_BUTTON_MIDDLE) or ctrl_left_mouse_down:
                mouse_delta = pr.get_mouse_delta()
                camera.target.x -= mouse_delta.x / camera.zoom
                camera.target.y -= mouse_delta.y / camera.zoom

            if current_mode == "simulation" and not simulation_boot_error:
                now = time.monotonic()
                activated_agents = engine.activate_due_agents(now)
                if activated_agents:
                    status_message = (
                        f"Activated {len(activated_agents)} shopper(s) | "
                        f"{len(engine.pending_spawns)} delayed remaining"
                    )

                resolved_status = resolve_completed_llm_requests(
                    engine,
                    simulation_config,
                    now,
                )
                if resolved_status:
                    status_message = resolved_status

                if action_runner is not None:
                    submitted_status = submit_due_llm_requests(
                        engine,
                        action_runner,
                        simulation_config,
                        now,
                    )
                    if submitted_status:
                        status_message = submitted_status

                if engine.should_save_results():
                    RESULTS_PATH.write_text(
                        json.dumps(engine.build_results_payload(), indent=2),
                        encoding="utf-8",
                    )
                    engine.simulation_results_saved = True
                    status_message = f"Saved simulation results to {RESULTS_PATH.name}"

            panel_click_handled = False
            if (
                current_mode == "products"
                and selected_shelf is not None
                and left_mouse_pressed
                and clicked_button is None
                and not clicked_load_products
                and pr.check_collision_point_rec(mouse_position, panel_rect)
            ):
                for shelf_type, button_rect in get_shelf_type_button_rects(
                    panel_rect
                ).items():
                    if pr.check_collision_point_rec(mouse_position, button_rect):
                        selected_shelf.type = shelf_type
                        panel_click_handled = True
                        break

                hovered_assigned_product = get_hovered_product_in_list(
                    top_list_rect,
                    selected_shelf.products,
                    assigned_list_view.scroll_offset,
                    mouse_position,
                )
                if not panel_click_handled and hovered_assigned_product is not None:
                    selected_shelf.products.remove(hovered_assigned_product)
                    panel_click_handled = True

                if not panel_click_handled:
                    available_products = get_available_products(products, selected_shelf)
                    hovered_available_product = get_hovered_product_in_list(
                        bottom_list_rect,
                        available_products,
                        available_list_view.scroll_offset,
                        mouse_position,
                    )
                    if hovered_available_product is not None:
                        selected_shelf.products.append(hovered_available_product)
                        panel_click_handled = True

            can_edit_layout = (
                current_mode == "layout"
                and not ctrl_down
                and clicked_button is None
                and not clicked_load_products
                and not clicked_save_layout
                and not clicked_load_layout
            )

            if can_edit_layout and pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                selection_start = hovered_cell
                selection_end = selection_start
                selection_mode = "add"

            if can_edit_layout and pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_RIGHT):
                selection_start = hovered_cell
                selection_end = selection_start
                selection_mode = "delete"

            if (
                selection_mode == "add"
                and selection_start is not None
                and pr.is_mouse_button_down(pr.MOUSE_BUTTON_LEFT)
            ):
                selection_end = hovered_cell

            if (
                selection_mode == "delete"
                and selection_start is not None
                and pr.is_mouse_button_down(pr.MOUSE_BUTTON_RIGHT)
            ):
                selection_end = hovered_cell

            if (
                selection_mode == "add"
                and selection_start is not None
                and selection_end is not None
                and pr.is_mouse_button_released(pr.MOUSE_BUTTON_LEFT)
            ):
                add_shelves(shelves, build_shelves(selection_start, selection_end))
                selection_start = None
                selection_end = None
                selection_mode = None

            if (
                selection_mode == "delete"
                and selection_start is not None
                and selection_end is not None
                and pr.is_mouse_button_released(pr.MOUSE_BUTTON_RIGHT)
            ):
                shelves = remove_shelves(
                    shelves,
                    build_shelves(selection_start, selection_end),
                )
                engine.shelves = shelves
                selection_start = None
                selection_end = None
                selection_mode = None

            if (
                current_mode == "products"
                and left_mouse_pressed
                and clicked_button is None
                and not clicked_load_products
                and not clicked_save_layout
                and not clicked_load_layout
                and not panel_click_handled
                and not pr.check_collision_point_rec(mouse_position, panel_rect)
            ):
                selected_shelf = hovered_shelf

            if (
                current_mode == "simulation"
                and left_mouse_pressed
                and clicked_button is None
                and not clicked_load_products
                and not clicked_save_layout
                and not clicked_load_layout
                and not pr.check_collision_point_rec(mouse_position, panel_rect)
            ):
                if clicked_agent is not None:
                    selected_agent_id = clicked_agent.customer_profile.customer_id
                else:
                    selected_agent_id = None

            pr.begin_drawing()
            pr.clear_background(pr.RAYWHITE)
            pr.begin_mode_2d(camera)
            draw_grid(GRID_SIZE, GRID_EXTENT)
            draw_origin_marker()
            draw_shelves(shelves, hovered_shelf, selected_shelf)
            if current_mode == "simulation":
                for agent in engine.active_agents:
                    draw_agent(agent)
                if selected_agent is not None:
                    draw_agent_selection(selected_agent)
            if current_mode == "layout":
                draw_cell_outline(hovered_cell, CELL_HOVER_COLOR)

            if selection_start is not None and selection_end is not None:
                is_single_click = selection_start == selection_end
                if not (selection_mode == "add" and is_single_click):
                    draw_selection_outline(selection_start, selection_end)
                    preview_color = (
                        SHELF_PREVIEW_COLOR
                        if selection_mode == "add"
                        else SHELF_DELETE_PREVIEW_COLOR
                    )
                    preview_shelves = build_shelves(selection_start, selection_end)
                    for shelf in preview_shelves:
                        draw_shelf(shelf, preview_color)
            pr.end_mode_2d()
            draw_button(
                top_action_button_rects["load_products"],
                "Load Products",
                is_hovered=pr.check_collision_point_rec(
                    mouse_position, top_action_button_rects["load_products"]
                ),
            )
            draw_button(
                top_action_button_rects["save_layout"],
                "Save Layout",
                is_hovered=pr.check_collision_point_rec(
                    mouse_position, top_action_button_rects["save_layout"]
                ),
            )
            draw_button(
                top_action_button_rects["load_layout"],
                "Load Layout",
                is_hovered=pr.check_collision_point_rec(
                    mouse_position, top_action_button_rects["load_layout"]
                ),
            )
            draw_button(
                button_rects["layout"],
                "Layout",
                current_mode == "layout",
                pr.check_collision_point_rec(mouse_position, button_rects["layout"]),
            )
            draw_button(
                button_rects["products"],
                "Products",
                current_mode == "products",
                pr.check_collision_point_rec(mouse_position, button_rects["products"]),
            )
            draw_button(
                button_rects["simulation"],
                "Simulation",
                current_mode == "simulation",
                pr.check_collision_point_rec(mouse_position, button_rects["simulation"]),
            )
            controls_text = "Middle mouse or Ctrl+Click: pan | Scroll wheel: zoom"
            if current_mode == "simulation":
                controls_text += (
                    f" | active {len(engine.active_agents)}"
                    f" | pending {len(engine.pending_spawns)}"
                    f" | in-flight {engine.count_in_flight_requests()}"
                    f" | completed {len(engine.completed_agents)}"
                )

            pr.draw_text(
                (
                    f"Mode: {current_mode.title()} | "
                    f"Products: {len(products)} | "
                    f"Revenue: {product_currency} {engine.get_total_revenue():.2f} | "
                    f"{controls_text}"
                ),
                20,
                get_status_text_y(),
                STATUS_PRIMARY_FONT_SIZE,
                pr.GRAY,
            )
            pr.draw_text(
                status_message,
                20,
                get_status_text_y() + 34,
                STATUS_SECONDARY_FONT_SIZE,
                pr.GRAY,
            )
            if current_mode == "simulation" and selected_agent is not None:
                draw_agent_panel(
                    panel_rect,
                    selected_agent,
                    product_currency,
                )
            elif current_mode in {"products", "simulation"} and panel_shelf is not None:
                draw_product_panel(
                    panel_rect,
                    panel_shelf,
                    products,
                    mouse_position,
                    current_mode == "products" and panel_shelf == selected_shelf,
                    product_currency,
                    assigned_list_view,
                    available_list_view,
                )
            elif current_mode == "products":
                pr.draw_text(
                    "Click a shelf to edit its products",
                    int(screen_width - PRODUCT_PANEL_WIDTH - PRODUCT_PANEL_MARGIN),
                    int(get_status_text_y() + 54),
                    PANEL_BODY_FONT_SIZE,
                    pr.GRAY,
                )
            elif current_mode == "simulation" and simulation_boot_error:
                pr.draw_text(
                    simulation_boot_error,
                    int(screen_width - PRODUCT_PANEL_WIDTH - PRODUCT_PANEL_MARGIN),
                    int(get_status_text_y() + 54),
                    PANEL_BODY_FONT_SIZE,
                    pr.GRAY,
                )
            elif (
                current_mode == "simulation"
                and not engine.active_agents
                and not engine.pending_spawns
            ):
                pr.draw_text(
                    "Simulation requires at least one entrance shelf",
                    int(screen_width - PRODUCT_PANEL_WIDTH - PRODUCT_PANEL_MARGIN),
                    int(get_status_text_y() + 54),
                    PANEL_BODY_FONT_SIZE,
                    pr.GRAY,
                )
            elif current_mode == "simulation":
                pr.draw_text(
                    "Click a shopper or hover a shelf",
                    int(screen_width - PRODUCT_PANEL_WIDTH - PRODUCT_PANEL_MARGIN),
                    int(get_status_text_y() + 54),
                    PANEL_BODY_FONT_SIZE,
                    pr.GRAY,
                )
            pr.end_drawing()
    finally:
        engine.reset_simulation()
        unload_list_view_texture(assigned_list_view)
        unload_list_view_texture(available_list_view)
        pr.close_window()
        if action_runner is not None:
            action_runner.close()

if __name__ == "__main__":
    main()
