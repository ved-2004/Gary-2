import time

import pyray as pr

from replay.state import ReplayAgent, ReplayState
from ui.controls import draw_button, get_status_text_y
from ui.panels import format_currency, wrap_panel_text
from ui.theme import (
    BUTTON_ACTIVE_COLOR,
    BUTTON_BORDER_COLOR,
    BUTTON_TEXT_COLOR,
    GRID_SIZE,
    PANEL_BODY_FONT_SIZE,
    PANEL_SECTION_GAP,
    PANEL_SECTION_TITLE_FONT_SIZE,
    PANEL_TITLE_FONT_SIZE,
    PANEL_NAME_FONT_SIZE,
    PRODUCT_PANEL_LINE_HEIGHT,
    PRODUCT_PANEL_PADDING,
    REPLAY_BTN_GAP,
    REPLAY_BTN_H,
    REPLAY_BTN_W,
    REPLAY_GROUP_GAP,
    REPLAY_SPEED_BTN_W,
    REPLAY_SPEED_OPTIONS,
    REPLAY_TIMELINE_H,
    REPLAY_TIMELINE_MARGIN_X,
    REPLAY_TRAIL_COLOR,
    REPLAY_TRAIL_DOT_RADIUS,
    REPLAY_TRAIL_LINE_WIDTH,
    SHOPPER_RADIUS,
    STATUS_SECONDARY_FONT_SIZE,
)


def find_replay_agent_at_world_position(
    agents: list[ReplayAgent],
    world_position: pr.Vector2,
) -> int | None:
    best_index: int | None = None
    best_dist_sq: float | None = None
    for i, agent in enumerate(agents):
        cx = agent.x * GRID_SIZE + GRID_SIZE / 2
        cy = agent.y * GRID_SIZE + GRID_SIZE / 2
        dx = world_position.x - cx
        dy = world_position.y - cy
        dist_sq = dx * dx + dy * dy
        if dist_sq > SHOPPER_RADIUS * SHOPPER_RADIUS:
            continue
        if best_dist_sq is None or dist_sq < best_dist_sq:
            best_index = i
            best_dist_sq = dist_sq
    return best_index


def draw_agent_trail(
    agent: ReplayAgent,
    current_step: int,
) -> None:
    if current_step < 0:
        return

    prev_x = agent.spawn_x
    prev_y = agent.spawn_y
    n = min(current_step + 1, len(agent.steps))
    for i in range(n):
        step = agent.steps[i]
        alpha = 0.15 + 0.85 * ((i + 1) / max(n, 1))
        x1 = prev_x * GRID_SIZE + GRID_SIZE // 2
        y1 = prev_y * GRID_SIZE + GRID_SIZE // 2
        x2 = step.position_x * GRID_SIZE + GRID_SIZE // 2
        y2 = step.position_y * GRID_SIZE + GRID_SIZE // 2
        color = pr.fade(REPLAY_TRAIL_COLOR, alpha)
        pr.draw_line_ex(
            pr.Vector2(float(x1), float(y1)),
            pr.Vector2(float(x2), float(y2)),
            REPLAY_TRAIL_LINE_WIDTH,
            color,
        )
        pr.draw_circle(x2, y2, REPLAY_TRAIL_DOT_RADIUS, color)
        prev_x = step.position_x
        prev_y = step.position_y


def get_replay_controls_y(screen_height: int) -> int:
    return get_status_text_y() - 86


def get_replay_timeline_y(screen_height: int) -> int:
    return get_status_text_y() - 40


def draw_replay_controls(
    replay_state: ReplayState,
    screen_width: int,
    screen_height: int,
    mouse_position: pr.Vector2,
) -> None:
    controls_y = get_replay_controls_y(screen_height)
    timeline_y = get_replay_timeline_y(screen_height)

    nav_width = REPLAY_BTN_W * 5 + REPLAY_BTN_GAP * 4
    speed_width = REPLAY_SPEED_BTN_W * len(REPLAY_SPEED_OPTIONS) + REPLAY_BTN_GAP * (
        len(REPLAY_SPEED_OPTIONS) - 1
    )
    total_width = nav_width + REPLAY_GROUP_GAP + speed_width
    start_x = (screen_width - total_width) / 2

    nav_labels = ["|<", "<", "Play" if not replay_state.is_playing else "Pause", ">", ">|"]
    for i in range(5):
        rect = pr.Rectangle(
            start_x + i * (REPLAY_BTN_W + REPLAY_BTN_GAP),
            controls_y,
            REPLAY_BTN_W,
            REPLAY_BTN_H,
        )
        is_hovered = pr.check_collision_point_rec(mouse_position, rect)
        draw_button(rect, nav_labels[i], is_hovered=is_hovered)

    speed_start_x = start_x + nav_width + REPLAY_GROUP_GAP
    for i, speed_val in enumerate(REPLAY_SPEED_OPTIONS):
        rect = pr.Rectangle(
            speed_start_x + i * (REPLAY_SPEED_BTN_W + REPLAY_BTN_GAP),
            controls_y,
            REPLAY_SPEED_BTN_W,
            REPLAY_BTN_H,
        )
        label = f"{speed_val:g}x"
        is_active = abs(replay_state.playback_speed - speed_val) < 0.01
        is_hovered = pr.check_collision_point_rec(mouse_position, rect)
        draw_button(rect, label, is_active=is_active, is_hovered=is_hovered)

    tl_x = REPLAY_TIMELINE_MARGIN_X
    tl_w = screen_width - REPLAY_TIMELINE_MARGIN_X * 2
    tl_rect = pr.Rectangle(tl_x, timeline_y, tl_w, REPLAY_TIMELINE_H)
    pr.draw_rectangle_rec(tl_rect, pr.fade(pr.LIGHTGRAY, 0.5))
    pr.draw_rectangle_lines_ex(tl_rect, 1, BUTTON_BORDER_COLOR)

    if replay_state.max_steps > 0:
        progress = (replay_state.current_step + 1) / replay_state.max_steps
        filled_w = max(0.0, tl_w * progress)
        pr.draw_rectangle_rec(
            pr.Rectangle(tl_x, timeline_y, filled_w, REPLAY_TIMELINE_H),
            pr.fade(BUTTON_ACTIVE_COLOR, 0.7),
        )
        cursor_x = tl_x + filled_w
        pr.draw_rectangle(
            int(cursor_x - 3), int(timeline_y - 3),
            6, REPLAY_TIMELINE_H + 6,
            BUTTON_BORDER_COLOR,
        )

    step_display = max(0, replay_state.current_step + 1)
    step_text = f"Step {step_display} / {replay_state.max_steps}"
    text_w = pr.measure_text(step_text, STATUS_SECONDARY_FONT_SIZE)
    pr.draw_text(
        step_text,
        int(screen_width - REPLAY_TIMELINE_MARGIN_X - text_w),
        int(timeline_y - 22),
        STATUS_SECONDARY_FONT_SIZE,
        BUTTON_TEXT_COLOR,
    )


def handle_replay_control_clicks(
    replay_state: ReplayState,
    screen_width: int,
    screen_height: int,
    mouse_position: pr.Vector2,
    left_clicked: bool,
    mouse_down: bool,
) -> None:
    if not left_clicked and not mouse_down:
        return

    controls_y = get_replay_controls_y(screen_height)
    timeline_y = get_replay_timeline_y(screen_height)

    if left_clicked:
        nav_width = REPLAY_BTN_W * 5 + REPLAY_BTN_GAP * 4
        speed_width = REPLAY_SPEED_BTN_W * len(REPLAY_SPEED_OPTIONS) + (
            REPLAY_BTN_GAP * (len(REPLAY_SPEED_OPTIONS) - 1)
        )
        total_width = nav_width + REPLAY_GROUP_GAP + speed_width
        start_x = (screen_width - total_width) / 2

        for i in range(5):
            rect = pr.Rectangle(
                start_x + i * (REPLAY_BTN_W + REPLAY_BTN_GAP),
                controls_y,
                REPLAY_BTN_W,
                REPLAY_BTN_H,
            )
            if pr.check_collision_point_rec(mouse_position, rect):
                if i == 0:
                    replay_state.reset()
                elif i == 1:
                    replay_state.step_backward()
                elif i == 2:
                    replay_state.toggle_play()
                    replay_state.last_step_time = time.monotonic()
                elif i == 3:
                    replay_state.step_forward()
                elif i == 4:
                    replay_state.go_to_end()
                return

        speed_start_x = start_x + nav_width + REPLAY_GROUP_GAP
        for i, speed_val in enumerate(REPLAY_SPEED_OPTIONS):
            rect = pr.Rectangle(
                speed_start_x + i * (REPLAY_SPEED_BTN_W + REPLAY_BTN_GAP),
                controls_y,
                REPLAY_SPEED_BTN_W,
                REPLAY_BTN_H,
            )
            if pr.check_collision_point_rec(mouse_position, rect):
                replay_state.playback_speed = speed_val
                return

    tl_x = float(REPLAY_TIMELINE_MARGIN_X)
    tl_w = float(screen_width - REPLAY_TIMELINE_MARGIN_X * 2)
    tl_rect = pr.Rectangle(tl_x, timeline_y, tl_w, REPLAY_TIMELINE_H + 6)
    if pr.check_collision_point_rec(mouse_position, tl_rect) and replay_state.max_steps > 0:
        ratio = max(0.0, min(1.0, (mouse_position.x - tl_x) / tl_w))
        target_step = int(ratio * replay_state.max_steps) - 1
        replay_state.seek(target_step)
        replay_state.is_playing = False


def draw_replay_agent_panel(
    panel_rect: pr.Rectangle,
    agent: ReplayAgent,
    replay_state: ReplayState,
    currency_code: str,
) -> None:
    pr.draw_rectangle_rec(panel_rect, pr.fade(pr.RAYWHITE, 0.96))
    pr.draw_rectangle_lines(
        int(panel_rect.x), int(panel_rect.y),
        int(panel_rect.width), int(panel_rect.height),
        BUTTON_BORDER_COLOR,
    )

    text_x = int(panel_rect.x + PRODUCT_PANEL_PADDING)
    text_width = int(panel_rect.width - PRODUCT_PANEL_PADDING * 2)
    line_y = int(panel_rect.y + PRODUCT_PANEL_PADDING)

    pr.draw_text("Shopper Replay", text_x, line_y, PANEL_TITLE_FONT_SIZE, BUTTON_TEXT_COLOR)
    line_y += 42
    pr.draw_text(agent.name, text_x, line_y, PANEL_NAME_FONT_SIZE, BUTTON_TEXT_COLOR)
    line_y += 36
    pr.draw_text(
        f"Position: ({agent.x}, {agent.y})",
        text_x, line_y, PANEL_BODY_FONT_SIZE, pr.GRAY,
    )
    line_y += 30

    step_info = replay_state.get_agent_step(agent)
    agent_total = len(agent.steps)
    agent_step_num = min(replay_state.current_step + 1, agent_total)
    pr.draw_text(
        f"Step: {agent_step_num} / {agent_total}",
        text_x, line_y, PANEL_BODY_FONT_SIZE, pr.GRAY,
    )
    line_y += 30

    if replay_state.current_step >= len(agent.steps):
        status_text = f"Finished: {agent.completion_reason.replace('_', ' ')}"
    else:
        status_text = "Active"
    pr.draw_text(
        f"Status: {status_text}",
        text_x, line_y, PANEL_BODY_FONT_SIZE, pr.GRAY,
    )
    line_y += 40

    if step_info is not None:
        action_color = pr.Color(50, 160, 50, 255) if step_info.success else pr.Color(200, 50, 50, 255)
        action_label = step_info.action
        if step_info.product_id:
            action_label += f" ({step_info.product_id})"
        if not step_info.success:
            action_label += " [failed]"
        pr.draw_text("Action", text_x, line_y, PANEL_SECTION_TITLE_FONT_SIZE, BUTTON_TEXT_COLOR)
        line_y += 34
        for wrapped in wrap_panel_text(action_label, text_width, PANEL_BODY_FONT_SIZE):
            pr.draw_text(wrapped, text_x, line_y, PANEL_BODY_FONT_SIZE, action_color)
            line_y += PRODUCT_PANEL_LINE_HEIGHT
        line_y += PANEL_SECTION_GAP

        pr.draw_text("Reasoning", text_x, line_y, PANEL_SECTION_TITLE_FONT_SIZE, BUTTON_TEXT_COLOR)
        line_y += 34
        reasoning = step_info.reasoning or "No reasoning recorded."
        for wrapped in wrap_panel_text(reasoning, text_width, PANEL_BODY_FONT_SIZE):
            pr.draw_text(wrapped, text_x, line_y, PANEL_BODY_FONT_SIZE, pr.GRAY)
            line_y += PRODUCT_PANEL_LINE_HEIGHT
        line_y += PANEL_SECTION_GAP

    pr.draw_text("Inventory", text_x, line_y, PANEL_SECTION_TITLE_FONT_SIZE, BUTTON_TEXT_COLOR)
    line_y += 34
    inv_items = step_info.inventory if step_info else []
    checked_items = step_info.checked_out_items if step_info else []
    if inv_items:
        for item in inv_items:
            item_text = (
                f"- {item.get('product_name', '?')} | "
                f"{item.get('company', '?')} | "
                f"{format_currency(float(item.get('selling_price', 0)), currency_code)}"
            )
            for wrapped in wrap_panel_text(item_text, text_width, PANEL_BODY_FONT_SIZE):
                pr.draw_text(wrapped, text_x, line_y, PANEL_BODY_FONT_SIZE, pr.GRAY)
                line_y += PRODUCT_PANEL_LINE_HEIGHT
        cart_total = sum(float(it.get("selling_price", 0)) for it in inv_items)
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
        pr.draw_text("No items in cart", text_x, line_y, PANEL_BODY_FONT_SIZE, pr.GRAY)
        line_y += PRODUCT_PANEL_LINE_HEIGHT

    if checked_items:
        line_y += 4
        purchased_total = sum(float(it.get("selling_price", 0)) for it in checked_items)
        pr.draw_text(
            f"Purchased total: {format_currency(purchased_total, currency_code)}",
            text_x,
            line_y,
            PANEL_BODY_FONT_SIZE,
            BUTTON_TEXT_COLOR,
        )
        line_y += PRODUCT_PANEL_LINE_HEIGHT

    line_y += PANEL_SECTION_GAP
    pr.draw_text("Shopping Targets", text_x, line_y, PANEL_SECTION_TITLE_FONT_SIZE, BUTTON_TEXT_COLOR)
    line_y += 34
    checked_names: set[str] = set()
    if step_info:
        for it in step_info.inventory:
            checked_names.add(str(it.get("product_name", "")))
        for it in step_info.checked_out_items:
            checked_names.add(str(it.get("product_name", "")))
    for target in agent.shopping_targets:
        found = target in checked_names
        marker = "[x]" if found else "[ ]"
        color = pr.Color(50, 160, 50, 255) if found else pr.GRAY
        pr.draw_text(f"{marker} {target}", text_x, line_y, PANEL_BODY_FONT_SIZE, color)
        line_y += PRODUCT_PANEL_LINE_HEIGHT
