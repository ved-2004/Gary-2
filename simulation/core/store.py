from __future__ import annotations

import math
from dataclasses import dataclass, field

import pyray as pr


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
