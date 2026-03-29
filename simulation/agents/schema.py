from typing import Literal
from pydantic import BaseModel

ALLOWED_LLM_ACTIONS = (
    "move_left",
    "move_right",
    "move_up",
    "move_down",
    "grab",
    "remove",
    "checkout",
)


class ShopperActionResponse(BaseModel):
    reasoning: str
    action: Literal[
        "move_left",
        "move_right",
        "move_up",
        "move_down",
        "grab",
        "remove",
        "checkout",
    ]
    product_id: str | None
