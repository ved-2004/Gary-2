import math

import pyray as pr

from agents import LLMAgent
from core.store import Product, ProductListView, Shelf

from ui.controls import draw_button, get_ui_row_y
from ui.theme import (
    BUTTON_BORDER_COLOR,
    BUTTON_COLOR,
    BUTTON_GAP,
    BUTTON_HEIGHT,
    BUTTON_TEXT_COLOR,
    PANEL_BODY_FONT_SIZE,
    PANEL_HINT_FONT_SIZE,
    PANEL_NAME_FONT_SIZE,
    PANEL_SECTION_GAP,
    PANEL_SECTION_TITLE_FONT_SIZE,
    PANEL_TITLE_FONT_SIZE,
    PRODUCT_ITEM_GAP,
    PRODUCT_ITEM_HEIGHT,
    PRODUCT_ITEM_HOVER_COLOR,
    PRODUCT_PANEL_HEADER_HEIGHT,
    PRODUCT_PANEL_LINE_HEIGHT,
    PRODUCT_PANEL_MARGIN,
    PRODUCT_PANEL_PADDING,
    PRODUCT_PANEL_WIDTH,
    PRODUCT_SECTION_GAP,
    PRODUCT_SECTION_HEADER_HEIGHT,
)


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
        cart_total = sum(item.selling_price for item in agent.inventory)
        line_y += 6
        pr.draw_text(
            f"Cart total (at checkout): {format_currency(cart_total, currency_code)}",
            text_x,
            line_y,
            PANEL_BODY_FONT_SIZE,
            BUTTON_TEXT_COLOR,
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
