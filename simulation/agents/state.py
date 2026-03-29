from dataclasses import dataclass

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
class CheckoutHint:
    target_x: int
    target_y: int
    delta_x: int
    delta_y: int
    manhattan_distance: int


@dataclass(frozen=True)
class NearbyShelfInfo:
    shelf_x: int
    shelf_y: int
    shelf_type: str
    manhattan_distance: int
    product_names: tuple[str, ...]


@dataclass(frozen=True)
class ActionRecord:
    action: str
    success: bool
    position_x: int
    position_y: int
    detail: str
    plan: str = ""


@dataclass
class TrajectoryStep:
    iteration: int
    position_before_x: int
    position_before_y: int
    raw_action: str
    raw_product_id: str | None
    raw_reasoning: str
    adjusted_action: str
    adjusted_product_id: str | None
    success: bool
    position_after_x: int
    position_after_y: int
    inventory_after: list[dict[str, object]]
    checked_out_items_after: list[dict[str, object]]


@dataclass(frozen=True)
class AgentState:
    allowed_actions: list[str]
    grabbable_items: list[GrabbableItem]
    can_checkout: bool
    nearest_checkout: CheckoutHint | None
    nearby_shelves: list[NearbyShelfInfo]


@dataclass(frozen=True)
class LLMAction:
    action: str
    product_id: str | None = None
    reasoning: str = ""
