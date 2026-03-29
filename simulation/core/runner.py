from agents import AsyncOpenAIActionRunner, CustomerProfile, LLMAction
from core.config import SimulationConfig
from core.engine import Engine


def start_simulation(
    engine: Engine,
    shopper_profiles: list[CustomerProfile],
    config: SimulationConfig,
    now: float,
    sprite_names: list[str],
) -> str:
    spawned_agents = engine.spawn_llm_agents(
        shopper_profiles,
        config,
        now,
        sprite_names,
    )
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
