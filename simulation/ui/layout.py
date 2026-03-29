import pyray as pr

from agents import Agent
from core.config import CHECKOUT_SPRITE_PATH, PEOPLE_SPRITES_DIR
from core.store import Shelf

from ui.theme import (
    GRID_EXTENT,
    GRID_POINT_COLOR,
    GRID_POINT_RADIUS,
    GRID_SIZE,
    ORIGIN_MARKER_COLOR,
    SELECTION_COLOR,
    SHELF_BORDER_COLOR,
    SHELF_DELETE_PREVIEW_COLOR,
    SHELF_HOVER_COLOR,
    SHELF_PADDING,
    SHELF_SELECTED_COLOR,
    SHELF_TYPE_CHECKOUT_COLOR,
    SHELF_TYPE_ENTRANCE_COLOR,
    SHELF_TYPE_SHELF_COLOR,
    SHOPPER_COLOR,
    SHOPPER_RADIUS,
    SHOPPER_SELECTED_COLOR,
)


def draw_grid(grid_size: int, extent: int) -> None:
    for x in range(-extent, extent + 1, grid_size):
        for y in range(-extent, extent + 1, grid_size):
            pr.draw_circle(x, y, GRID_POINT_RADIUS, GRID_POINT_COLOR)


def get_shelf_type_color(shelf_type: str) -> pr.Color:
    if shelf_type == "checkout":
        return SHELF_TYPE_CHECKOUT_COLOR
    if shelf_type == "entrance":
        return SHELF_TYPE_ENTRANCE_COLOR
    return SHELF_TYPE_SHELF_COLOR


def load_checkout_texture() -> object | None:
    if not CHECKOUT_SPRITE_PATH.exists():
        return None
    return pr.load_texture(str(CHECKOUT_SPRITE_PATH))


def unload_checkout_texture(checkout_texture: object | None) -> None:
    if checkout_texture is not None:
        pr.unload_texture(checkout_texture)


def draw_shelf(
    shelf: Shelf,
    color: pr.Color,
    checkout_texture: object | None = None,
) -> None:
    x = shelf.x * GRID_SIZE + SHELF_PADDING
    y = shelf.y * GRID_SIZE + SHELF_PADDING
    size = GRID_SIZE - SHELF_PADDING * 2
    if shelf.type == "checkout" and checkout_texture is not None:
        pr.draw_texture_pro(
            checkout_texture,
            pr.Rectangle(
                0,
                0,
                float(checkout_texture.width),
                float(checkout_texture.height),
            ),
            pr.Rectangle(float(x), float(y), float(size), float(size)),
            pr.Vector2(0, 0),
            0.0,
            pr.WHITE,
        )
        return
    pr.draw_rectangle(x, y, size, size, color)


def draw_shelves(
    shelves: list[Shelf],
    hovered_shelf: Shelf | None = None,
    selected_shelf: Shelf | None = None,
    checkout_texture: object | None = None,
) -> None:
    for shelf in shelves:
        color = get_shelf_type_color(shelf.type)
        draw_shelf(shelf, color, checkout_texture)
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


def load_agent_sprites() -> dict[str, object]:
    textures: dict[str, object] = {}
    if not PEOPLE_SPRITES_DIR.exists():
        return textures

    for sprite_path in sorted(PEOPLE_SPRITES_DIR.glob("*.png")):
        textures[sprite_path.name] = pr.load_texture(str(sprite_path))
    return textures


def unload_agent_sprites(agent_sprites: dict[str, object]) -> None:
    for texture in agent_sprites.values():
        pr.unload_texture(texture)


def draw_agent(agent: Agent, agent_sprites: dict[str, object]) -> None:
    texture = agent_sprites.get(agent.sprite_name)
    if texture is None:
        center_x = agent.x * GRID_SIZE + GRID_SIZE / 2
        center_y = agent.y * GRID_SIZE + GRID_SIZE / 2
        pr.draw_circle(int(center_x), int(center_y), SHOPPER_RADIUS, SHOPPER_COLOR)
        return

    draw_x = float(agent.x * GRID_SIZE)
    draw_y = float(agent.y * GRID_SIZE)
    pr.draw_texture_pro(
        texture,
        pr.Rectangle(0, 0, float(texture.width), float(texture.height)),
        pr.Rectangle(draw_x, draw_y, float(GRID_SIZE), float(GRID_SIZE)),
        pr.Vector2(0, 0),
        0.0,
        pr.WHITE,
    )


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
