import json
import random
import time
from pathlib import Path

import pyray as pr

from agents import AsyncOpenAIActionRunner, CustomerProfile
from core.cli import parse_cli_args
from core.config import DEFAULT_OPENAI_TIMEOUT_SECONDS, RESULTS_PATH
from core.customers import load_customer_profiles
from core.engine import Engine
from core.env import get_openai_api_key
from core.persistence import (
    load_layout_from_json,
    load_products_from_json,
    pick_layout_load_file,
    pick_layout_save_file,
    pick_products_file,
    save_layout_to_json,
)
from core.runner import (
    resolve_completed_llm_requests,
    start_simulation,
    submit_due_llm_requests,
)
from core.store import (
    Product,
    ProductListView,
    Shelf,
    add_shelves,
    build_shelves,
    find_shelf_at_cell,
    get_cell_at_position,
    remove_shelves,
)
from replay.io import load_trajectory, pick_trajectory_file, save_trajectory
from replay.state import ReplayAgent, ReplayState
from replay.ui import (
    draw_agent_trail,
    draw_replay_agent_panel,
    draw_replay_controls,
    find_replay_agent_at_world_position,
    handle_replay_control_clicks,
)
from ui.controls import (
    draw_button,
    get_mode_button_rects,
    get_status_text_y,
    get_top_action_button_rects,
)
from ui.layout import (
    draw_agent,
    draw_agent_selection,
    draw_cell_outline,
    draw_grid,
    draw_origin_marker,
    draw_shelf,
    draw_shelves,
    draw_selection_outline,
    find_agent_at_world_position,
    load_agent_sprites,
    load_checkout_texture,
    unload_agent_sprites,
    unload_checkout_texture,
)
from ui.panels import (
    clamp_scroll_offset,
    draw_agent_panel,
    draw_product_panel,
    get_available_products,
    get_hovered_product_in_list,
    get_panel_products,
    get_product_list_content_height,
    get_product_panel_rect,
    get_product_panel_sections,
    get_shelf_type_button_rects,
    unload_list_view_texture,
)
from ui.product_images import load_product_textures, unload_product_textures
from ui.theme import (
    CELL_HOVER_COLOR,
    GRID_EXTENT,
    GRID_SIZE,
    MAX_ZOOM,
    MIN_ZOOM,
    PANEL_BODY_FONT_SIZE,
    PRODUCT_PANEL_MARGIN,
    PRODUCT_PANEL_WIDTH,
    SHELF_DELETE_PREVIEW_COLOR,
    SHELF_PREVIEW_COLOR,
    SHOPPER_RADIUS,
    STATUS_PRIMARY_FONT_SIZE,
    STATUS_SECONDARY_FONT_SIZE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


def main() -> None:
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
    product_search_query = ""
    active_panel_shelf_key: tuple[int, int] | None = None
    agent_sprites = load_agent_sprites()
    product_textures = load_product_textures()
    sprite_names = list(agent_sprites.keys())
    checkout_texture = load_checkout_texture()
    replay_state: ReplayState | None = None
    replay_shelves: list[Shelf] = []
    replay_products: list[Product] = []
    replay_currency: str = "USD"
    replay_selected_idx: int | None = None
    trajectory_saved_this_run: bool = False

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
            clicked_load_replay = False

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

            if (
                clicked_button is None
                and not clicked_load_products
                and not clicked_save_layout
                and not clicked_load_layout
                and left_mouse_pressed
                and pr.check_collision_point_rec(
                    mouse_position, top_action_button_rects["load_replay"]
                )
            ):
                clicked_load_replay = True

            if clicked_button is not None:
                if clicked_button != "products":
                    product_search_query = ""
                current_mode = clicked_button
                selection_start = None
                selection_end = None
                selection_mode = None
                if current_mode != "simulation":
                    selected_agent_id = None
                if current_mode == "replay":
                    replay_selected_idx = None
                    engine.reset_simulation()
                    if replay_state is not None:
                        replay_state.is_playing = False
                        status_message = (
                            f"Replay loaded: {len(replay_state.agents)} agents, "
                            f"{replay_state.max_steps} steps"
                        )
                    else:
                        status_message = "No trajectory loaded. Click Load Replay."
                elif current_mode == "simulation":
                    trajectory_saved_this_run = False
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
                                sprite_names,
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
                product_search_query = ""
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
                        product_search_query = ""
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
                                    sprite_names,
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
                product_search_query = ""
                selection_start = None
                selection_end = None
                selection_mode = None

            if clicked_load_replay:
                try:
                    selected_path = pick_trajectory_file()
                    if selected_path:
                        (
                            replay_shelves,
                            replay_products,
                            replay_currency,
                            replay_state,
                        ) = load_trajectory(selected_path)
                        replay_selected_idx = None
                        current_mode = "replay"
                        engine.reset_simulation()
                        status_message = (
                            f"Loaded trajectory: {len(replay_state.agents)} agents, "
                            f"{replay_state.max_steps} steps from "
                            f"{Path(selected_path).name}"
                        )
                    else:
                        status_message = "Trajectory load canceled"
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    status_message = f"Failed to load trajectory: {exc}"
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
            active_shelves = replay_shelves if current_mode == "replay" else shelves
            hovered_shelf = find_shelf_at_cell(active_shelves, hovered_cell)
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

            panel_assigned_products: list[Product] = []
            panel_available_products: list[Product] = []
            if panel_shelf is not None:
                search_query = product_search_query if current_mode == "products" else ""
                panel_assigned_products = get_panel_products(
                    panel_shelf.products,
                    search_query,
                )
                panel_available_products = get_panel_products(
                    get_available_products(products, panel_shelf),
                    search_query,
                )

            if current_mode == "products" and selected_shelf is not None and not ctrl_down:
                updated_search_query = product_search_query
                if pr.is_key_pressed(pr.KEY_BACKSPACE) and updated_search_query:
                    updated_search_query = updated_search_query[:-1]
                elif pr.is_key_pressed(pr.KEY_ESCAPE) and updated_search_query:
                    updated_search_query = ""

                while True:
                    codepoint = pr.get_char_pressed()
                    if codepoint == 0:
                        break
                    if 32 <= codepoint <= 126:
                        updated_search_query += chr(codepoint)

                if updated_search_query != product_search_query:
                    product_search_query = updated_search_query[:60]
                    assigned_list_view.scroll_offset = 0.0
                    available_list_view.scroll_offset = 0.0
                    panel_assigned_products = get_panel_products(
                        selected_shelf.products,
                        product_search_query,
                    )
                    panel_available_products = get_panel_products(
                        get_available_products(products, selected_shelf),
                        product_search_query,
                    )

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
                        get_product_list_content_height(panel_assigned_products),
                    )
                    mouse_wheel = 0
                elif pr.check_collision_point_rec(mouse_position, bottom_list_rect):
                    available_list_view.scroll_offset -= mouse_wheel * 40
                    available_list_view.scroll_offset = clamp_scroll_offset(
                        available_list_view.scroll_offset,
                        bottom_list_rect.height,
                        get_product_list_content_height(panel_available_products),
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

                    if not trajectory_saved_this_run:
                        try:
                            traj_path = save_trajectory(
                                engine, simulation_config, products, product_currency,
                            )
                            trajectory_saved_this_run = True
                            status_message = (
                                f"Saved results + trajectory to {traj_path.name}"
                            )
                        except (OSError, ValueError) as exc:
                            status_message = (
                                f"Results saved, trajectory failed: {exc}"
                            )

            if current_mode == "replay" and replay_state is not None:
                now = time.monotonic()
                if replay_state.is_playing and replay_state.max_steps > 0:
                    step_interval = 1.0 / replay_state.playback_speed
                    if now - replay_state.last_step_time >= step_interval:
                        replay_state.step_forward()
                        replay_state.last_step_time = now
                        if replay_state.current_step >= replay_state.max_steps - 1:
                            replay_state.is_playing = False

                if pr.is_key_pressed(pr.KEY_SPACE):
                    replay_state.toggle_play()
                    replay_state.last_step_time = now
                if pr.is_key_pressed(pr.KEY_RIGHT):
                    replay_state.step_forward()
                    replay_state.is_playing = False
                if pr.is_key_pressed(pr.KEY_LEFT):
                    replay_state.step_backward()
                    replay_state.is_playing = False
                if pr.is_key_pressed(pr.KEY_HOME):
                    replay_state.reset()
                if pr.is_key_pressed(pr.KEY_END):
                    replay_state.go_to_end()

                handle_replay_control_clicks(
                    replay_state, screen_width, screen_height,
                    mouse_position, left_mouse_pressed,
                    pr.is_mouse_button_down(pr.MOUSE_BUTTON_LEFT),
                )

                if (
                    left_mouse_pressed
                    and clicked_button is None
                    and not clicked_load_replay
                    and not pr.check_collision_point_rec(mouse_position, panel_rect)
                ):
                    hit = find_replay_agent_at_world_position(
                        replay_state.agents, mouse_world_position,
                    )
                    replay_selected_idx = hit

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
                    panel_assigned_products,
                    assigned_list_view.scroll_offset,
                    mouse_position,
                )
                if not panel_click_handled and hovered_assigned_product is not None:
                    selected_shelf.products.remove(hovered_assigned_product)
                    panel_click_handled = True

                if not panel_click_handled:
                    hovered_available_product = get_hovered_product_in_list(
                        bottom_list_rect,
                        panel_available_products,
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

            selected_replay_agent: ReplayAgent | None = None
            if current_mode == "replay" and replay_state is not None and replay_selected_idx is not None:
                if 0 <= replay_selected_idx < len(replay_state.agents):
                    selected_replay_agent = replay_state.agents[replay_selected_idx]

            pr.begin_drawing()
            pr.clear_background(pr.RAYWHITE)
            pr.begin_mode_2d(camera)
            draw_grid(GRID_SIZE, GRID_EXTENT)
            draw_origin_marker()
            draw_shelves(
                active_shelves,
                hovered_shelf,
                selected_shelf if current_mode != "replay" else None,
                checkout_texture,
                product_textures,
            )
            if current_mode == "simulation":
                for agent in engine.active_agents:
                    draw_agent(agent, agent_sprites)
                if selected_agent is not None:
                    draw_agent_selection(selected_agent)
            if current_mode == "replay" and replay_state is not None:
                if selected_replay_agent is not None:
                    draw_agent_trail(selected_replay_agent, replay_state.current_step)
                for r_agent in replay_state.agents:
                    is_done = not replay_state.is_agent_active_at_step(r_agent)
                    draw_agent(r_agent, agent_sprites)
                    if is_done:
                        cx = r_agent.x * GRID_SIZE + GRID_SIZE // 2
                        cy = r_agent.y * GRID_SIZE + GRID_SIZE // 2
                        pr.draw_circle(cx, cy, SHOPPER_RADIUS + 2, pr.fade(pr.GRAY, 0.4))
                if selected_replay_agent is not None:
                    draw_agent_selection(selected_replay_agent)
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
                top_action_button_rects["load_replay"],
                "Load Replay",
                is_hovered=pr.check_collision_point_rec(
                    mouse_position, top_action_button_rects["load_replay"]
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
            draw_button(
                button_rects["replay"],
                "Replay",
                current_mode == "replay",
                pr.check_collision_point_rec(mouse_position, button_rects["replay"]),
            )
            controls_text = "Middle mouse or Ctrl+Click: pan | Scroll wheel: zoom"
            if current_mode == "simulation":
                controls_text += (
                    f" | active {len(engine.active_agents)}"
                    f" | pending {len(engine.pending_spawns)}"
                    f" | in-flight {engine.count_in_flight_requests()}"
                    f" | completed {len(engine.completed_agents)}"
                )
            elif current_mode == "replay":
                controls_text += " | Space: play/pause | Arrows: step | Home/End: jump"

            pr.draw_text(
                (
                    f"Mode: {current_mode.title()} | "
                    f"Products: {len(active_shelves)} shelves | "
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
            if current_mode == "replay" and replay_state is not None:
                draw_replay_controls(
                    replay_state, screen_width, screen_height, mouse_position,
                )
                if selected_replay_agent is not None:
                    draw_replay_agent_panel(
                        panel_rect, selected_replay_agent,
                        replay_state, replay_currency,
                    )
                elif replay_state.max_steps == 0:
                    pr.draw_text(
                        "No trajectory loaded. Click Load Replay.",
                        int(screen_width - PRODUCT_PANEL_WIDTH - PRODUCT_PANEL_MARGIN),
                        int(get_status_text_y() + 54),
                        PANEL_BODY_FONT_SIZE,
                        pr.GRAY,
                    )
                else:
                    pr.draw_text(
                        "Click a shopper to view details",
                        int(screen_width - PRODUCT_PANEL_WIDTH - PRODUCT_PANEL_MARGIN),
                        int(get_status_text_y() + 54),
                        PANEL_BODY_FONT_SIZE,
                        pr.GRAY,
                    )
            elif current_mode == "simulation" and selected_agent is not None:
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
                    product_search_query if current_mode == "products" else "",
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
        unload_checkout_texture(checkout_texture)
        unload_agent_sprites(agent_sprites)
        unload_product_textures(product_textures)
        unload_list_view_texture(assigned_list_view)
        unload_list_view_texture(available_list_view)
        pr.close_window()
        if action_runner is not None:
            action_runner.close()


if __name__ == "__main__":
    main()
