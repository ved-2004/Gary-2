from dataclasses import dataclass
from pathlib import Path

SIMULATION_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = SIMULATION_DIR.parent
DATA_DIR = ROOT_DIR / "data"
ROOT_ENV_PATH = ROOT_DIR / ".env"
CUSTOMER_PROFILES_PATH = DATA_DIR / "customer_profiles.csv"
SHOPPING_LIST_PATH = DATA_DIR / "shopping_list.csv"
RESULTS_PATH = SIMULATION_DIR / "results.json"
TRAJECTORY_DIR = SIMULATION_DIR / "trajectory"
PEOPLE_SPRITES_DIR = ROOT_DIR / "Sprites" / "PeopleSprites"
CHECKOUT_SPRITE_PATH = ROOT_DIR / "Sprites" / "checkout.png"

MAX_LLM_AGENT_COUNT = 15
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_REASONING_EFFORT = "none"
DEFAULT_ACTION_COOLDOWN_SECONDS = 2.0
DEFAULT_SPAWN_DELAY_WINDOW_SECONDS = 0.0
DEFAULT_OPENAI_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_ITERATIONS_PER_AGENT = 100
SUPPORTED_REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh")

JSON_FILE_FILTERS = [("JSON files", "*.json"), ("All files", "*.*")]


@dataclass(frozen=True)
class SimulationConfig:
    agent_count: int = MAX_LLM_AGENT_COUNT
    model: str = DEFAULT_MODEL
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT
    action_cooldown_seconds: float = DEFAULT_ACTION_COOLDOWN_SECONDS
    spawn_delay_window_seconds: float = DEFAULT_SPAWN_DELAY_WINDOW_SECONDS
    max_iterations_per_agent: int = DEFAULT_MAX_ITERATIONS_PER_AGENT
    max_concurrency: int = MAX_LLM_AGENT_COUNT
    seed: int | None = None
