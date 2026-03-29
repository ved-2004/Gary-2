from dataclasses import dataclass, field


@dataclass
class ReplayStep:
    action: str
    product_id: str | None
    reasoning: str
    raw_action: str
    success: bool
    position_x: int
    position_y: int
    inventory: list[dict[str, object]]
    checked_out_items: list[dict[str, object]]


@dataclass
class ReplayAgent:
    customer_id: str
    name: str
    sprite_name: str
    spawn_x: int
    spawn_y: int
    shopping_targets: list[str]
    unavailable_targets: list[str]
    completion_reason: str
    steps: list[ReplayStep] = field(default_factory=list)
    x: int = 0
    y: int = 0


@dataclass
class ReplayState:
    agents: list[ReplayAgent] = field(default_factory=list)
    max_steps: int = 0
    current_step: int = -1
    is_playing: bool = False
    playback_speed: float = 2.0
    last_step_time: float = 0.0

    def seek(self, step: int) -> None:
        self.current_step = max(-1, min(step, self.max_steps - 1))
        self._sync_positions()

    def step_forward(self) -> None:
        if self.current_step < self.max_steps - 1:
            self.current_step += 1
            self._sync_positions()

    def step_backward(self) -> None:
        if self.current_step >= 0:
            self.current_step -= 1
            self._sync_positions()

    def toggle_play(self) -> None:
        self.is_playing = not self.is_playing
        if self.is_playing and self.current_step >= self.max_steps - 1:
            self.seek(-1)

    def reset(self) -> None:
        self.seek(-1)
        self.is_playing = False

    def go_to_end(self) -> None:
        self.seek(self.max_steps - 1)
        self.is_playing = False

    def _sync_positions(self) -> None:
        for agent in self.agents:
            if self.current_step < 0:
                agent.x = agent.spawn_x
                agent.y = agent.spawn_y
            elif self.current_step < len(agent.steps):
                step = agent.steps[self.current_step]
                agent.x = step.position_x
                agent.y = step.position_y
            elif agent.steps:
                last_step = agent.steps[-1]
                agent.x = last_step.position_x
                agent.y = last_step.position_y
            else:
                agent.x = agent.spawn_x
                agent.y = agent.spawn_y

    def get_agent_step(self, agent: ReplayAgent) -> ReplayStep | None:
        if 0 <= self.current_step < len(agent.steps):
            return agent.steps[self.current_step]
        return None

    def is_agent_active_at_step(self, agent: ReplayAgent) -> bool:
        return self.current_step < len(agent.steps)
