import argparse

from core.config import (
    DEFAULT_ACTION_COOLDOWN_SECONDS,
    DEFAULT_MAX_ITERATIONS_PER_AGENT,
    DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT,
    DEFAULT_SPAWN_DELAY_WINDOW_SECONDS,
    MAX_LLM_AGENT_COUNT,
    SUPPORTED_REASONING_EFFORTS,
    SimulationConfig,
)


def parse_agent_count(value: str) -> int:
    parsed_value = int(value)
    if parsed_value < 1 or parsed_value > MAX_LLM_AGENT_COUNT:
        raise argparse.ArgumentTypeError(
            f"Agent count must be between 1 and {MAX_LLM_AGENT_COUNT}."
        )
    return parsed_value


def parse_non_negative_float(value: str) -> float:
    parsed_value = float(value)
    if parsed_value < 0:
        raise argparse.ArgumentTypeError("Value must be non-negative.")
    return parsed_value


def parse_positive_int(value: str) -> int:
    parsed_value = int(value)
    if parsed_value < 1:
        raise argparse.ArgumentTypeError("Value must be at least 1.")
    return parsed_value


def validate_reasoning_effort(model: str, reasoning_effort: str | None) -> None:
    if reasoning_effort is None:
        return

    normalized_model = model.strip().lower()
    if normalized_model.startswith("gpt-5-mini"):
        raise argparse.ArgumentTypeError(
            "gpt-5-mini uses fixed medium reasoning and does not support "
            "--reasoning-effort overrides."
        )

    if normalized_model.startswith("gpt-5.4"):
        allowed = {"none", "low", "medium", "high", "xhigh"}
    elif normalized_model.startswith("gpt-5.1"):
        allowed = {"none", "low", "medium", "high"}
    elif normalized_model.startswith("gpt-5-pro"):
        allowed = {"high"}
    elif normalized_model == "gpt-5" or normalized_model.startswith("gpt-5-"):
        allowed = {"minimal", "low", "medium", "high"}
    else:
        return

    if reasoning_effort not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise argparse.ArgumentTypeError(
            f"{model} supports reasoning efforts: {allowed_text}."
        )


def parse_cli_args() -> SimulationConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--agent-count",
        type=parse_agent_count,
        default=MAX_LLM_AGENT_COUNT,
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=SUPPORTED_REASONING_EFFORTS,
        default=DEFAULT_REASONING_EFFORT,
    )
    parser.add_argument(
        "--action-cooldown-seconds",
        type=parse_non_negative_float,
        default=DEFAULT_ACTION_COOLDOWN_SECONDS,
    )
    parser.add_argument(
        "--spawn-delay-window-seconds",
        type=parse_non_negative_float,
        default=DEFAULT_SPAWN_DELAY_WINDOW_SECONDS,
    )
    parser.add_argument(
        "--max-iterations-per-agent",
        type=parse_positive_int,
        default=DEFAULT_MAX_ITERATIONS_PER_AGENT,
    )
    parser.add_argument(
        "--max-concurrency",
        type=parse_positive_int,
        default=MAX_LLM_AGENT_COUNT,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
    )
    args = parser.parse_args()
    try:
        validate_reasoning_effort(args.model, args.reasoning_effort)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    max_concurrency = min(args.max_concurrency, args.agent_count, MAX_LLM_AGENT_COUNT)
    return SimulationConfig(
        agent_count=args.agent_count,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        action_cooldown_seconds=args.action_cooldown_seconds,
        spawn_delay_window_seconds=args.spawn_delay_window_seconds,
        max_iterations_per_agent=args.max_iterations_per_agent,
        max_concurrency=max_concurrency,
        seed=args.seed,
    )
