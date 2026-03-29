import pyray as pr
from ui.theme import (
    BUTTON_BORDER_COLOR,
    BUTTON_COLOR,
    BUTTON_GAP,
    BUTTON_HEIGHT,
    BUTTON_ACTIVE_COLOR,
    BUTTON_HOVER_COLOR,
    BUTTON_TEXT_COLOR,
    BUTTON_TEXT_SIZE,
    BUTTON_TOP_MARGIN,
    BUTTON_ROW_GAP,
    LAYOUT_BUTTON_WIDTH,
    LOAD_BUTTON_WIDTH,
    LOAD_REPLAY_BUTTON_WIDTH,
    MODE_BUTTON_WIDTH,
)


def get_ui_row_y(row_index: int) -> int:
    return BUTTON_TOP_MARGIN + row_index * (BUTTON_HEIGHT + BUTTON_ROW_GAP)


def get_status_text_y() -> int:
    return pr.get_screen_height() - 84


def get_mode_button_rects(screen_width: int) -> dict[str, pr.Rectangle]:
    total_width = MODE_BUTTON_WIDTH * 4 + BUTTON_GAP * 3
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
        "replay": pr.Rectangle(
            start_x + (MODE_BUTTON_WIDTH + BUTTON_GAP) * 3,
            get_ui_row_y(1),
            MODE_BUTTON_WIDTH,
            BUTTON_HEIGHT,
        ),
    }


def get_top_action_button_rects(screen_width: int) -> dict[str, pr.Rectangle]:
    total_width = (
        LOAD_BUTTON_WIDTH + LAYOUT_BUTTON_WIDTH * 2
        + LOAD_REPLAY_BUTTON_WIDTH + BUTTON_GAP * 3
    )
    start_x = (screen_width - total_width) / 2
    x_cursor = start_x
    rects: dict[str, pr.Rectangle] = {}
    rects["load_products"] = pr.Rectangle(x_cursor, get_ui_row_y(0), LOAD_BUTTON_WIDTH, BUTTON_HEIGHT)
    x_cursor += LOAD_BUTTON_WIDTH + BUTTON_GAP
    rects["save_layout"] = pr.Rectangle(x_cursor, get_ui_row_y(0), LAYOUT_BUTTON_WIDTH, BUTTON_HEIGHT)
    x_cursor += LAYOUT_BUTTON_WIDTH + BUTTON_GAP
    rects["load_layout"] = pr.Rectangle(x_cursor, get_ui_row_y(0), LAYOUT_BUTTON_WIDTH, BUTTON_HEIGHT)
    x_cursor += LAYOUT_BUTTON_WIDTH + BUTTON_GAP
    rects["load_replay"] = pr.Rectangle(x_cursor, get_ui_row_y(0), LOAD_REPLAY_BUTTON_WIDTH, BUTTON_HEIGHT)
    return rects


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
