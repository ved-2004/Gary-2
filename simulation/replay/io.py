import json
import time
from pathlib import Path

from plyer import filechooser

from agents import LLMAgent
from core.config import JSON_FILE_FILTERS, SimulationConfig, TRAJECTORY_DIR
from core.engine import Engine
from core.persistence import choose_single_file, parse_layout_data, product_to_dict, shelf_to_dict
from core.store import Product, Shelf

from replay.state import ReplayAgent, ReplayState, ReplayStep


def save_trajectory(
    engine: Engine,
    config: SimulationConfig,
    products: list[Product],
    currency: str,
) -> Path:
    TRAJECTORY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filepath = TRAJECTORY_DIR / f"trajectory_{timestamp}.json"

    agents_data: list[dict] = []
    all_agents = list(engine.completed_agents) + list(engine.active_agents)
    for agent in all_agents:
        if not isinstance(agent, LLMAgent):
            continue
        steps_data: list[dict] = []
        for step in agent.trajectory_steps:
            steps_data.append({
                "iteration": step.iteration,
                "position_before": {
                    "x": step.position_before_x,
                    "y": step.position_before_y,
                },
                "raw_action": step.raw_action,
                "raw_product_id": step.raw_product_id,
                "raw_reasoning": step.raw_reasoning,
                "adjusted_action": step.adjusted_action,
                "adjusted_product_id": step.adjusted_product_id,
                "success": step.success,
                "position_after": {
                    "x": step.position_after_x,
                    "y": step.position_after_y,
                },
                "inventory_after": step.inventory_after,
                "checked_out_items_after": step.checked_out_items_after,
            })
        agents_data.append({
            "customer_id": agent.customer_profile.customer_id,
            "name": agent.name,
            "sprite_name": agent.sprite_name,
            "spawn_position": {
                "x": agent.trajectory_spawn_x,
                "y": agent.trajectory_spawn_y,
            },
            "shopping_targets": agent.shopping_targets,
            "unavailable_targets": agent.unavailable_targets,
            "max_iterations": agent.max_iterations,
            "completion_reason": agent.completion_reason,
            "steps": steps_data,
        })

    data = {
        "metadata": {
            "timestamp": timestamp,
            "model": config.model,
            "reasoning_effort": config.reasoning_effort,
            "agent_count": config.agent_count,
            "max_iterations_per_agent": config.max_iterations_per_agent,
            "seed": config.seed,
        },
        "layout": {
            "currency": currency,
            "products": [product_to_dict(p) for p in products],
            "shelves": [shelf_to_dict(s) for s in engine.shelves],
        },
        "agents": agents_data,
    }
    filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return filepath


def load_trajectory(path: str) -> tuple[list[Shelf], list[Product], str, ReplayState]:
    with Path(path).open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Trajectory JSON must contain a top-level object.")

    layout_data = data.get("layout")
    if not isinstance(layout_data, dict):
        raise ValueError("Trajectory JSON must contain a 'layout' object.")

    shelves, products, currency = parse_layout_data(layout_data)

    raw_agents = data.get("agents", [])
    replay_agents: list[ReplayAgent] = []
    for agent_data in raw_agents:
        steps: list[ReplayStep] = []
        for step_data in agent_data.get("steps", []):
            pos_after = step_data.get("position_after", {})
            steps.append(ReplayStep(
                action=step_data.get("adjusted_action", ""),
                product_id=step_data.get("adjusted_product_id"),
                reasoning=step_data.get("raw_reasoning", ""),
                raw_action=step_data.get("raw_action", ""),
                success=step_data.get("success", False),
                position_x=int(pos_after.get("x", 0)),
                position_y=int(pos_after.get("y", 0)),
                inventory=step_data.get("inventory_after", []),
                checked_out_items=step_data.get("checked_out_items_after", []),
            ))
        spawn = agent_data.get("spawn_position", {})
        spawn_x = int(spawn.get("x", 0))
        spawn_y = int(spawn.get("y", 0))
        replay_agents.append(ReplayAgent(
            customer_id=agent_data.get("customer_id", ""),
            name=agent_data.get("name", ""),
            sprite_name=agent_data.get("sprite_name", ""),
            spawn_x=spawn_x,
            spawn_y=spawn_y,
            shopping_targets=agent_data.get("shopping_targets", []),
            unavailable_targets=agent_data.get("unavailable_targets", []),
            completion_reason=agent_data.get("completion_reason", ""),
            steps=steps,
            x=spawn_x,
            y=spawn_y,
        ))

    max_steps = max((len(a.steps) for a in replay_agents), default=0)
    state = ReplayState(agents=replay_agents, max_steps=max_steps)
    return shelves, products, currency, state


def pick_trajectory_file() -> str:
    TRAJECTORY_DIR.mkdir(parents=True, exist_ok=True)
    selected_path = filechooser.open_file(
        path=str(TRAJECTORY_DIR),
        title="Select trajectory JSON",
        filters=JSON_FILE_FILTERS,
    )
    return choose_single_file(selected_path)
