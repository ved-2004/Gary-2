"use client";

import { useEffect, useEffectEvent, useId, useState } from "react";
import type {
  ReplayAgent,
  ReplayBounds,
  ReplayCartItem,
  ReplayTrajectory,
} from "@/lib/replay";
import {
  formatCompletionReason,
  formatCurrency,
  getAgentSpritePath,
  getReplayAgentSnapshot,
  getReplayBounds,
  getReplayStepLabel,
} from "@/lib/replay";

export interface ReplayCatalogEntry {
  id: string;
  label: string;
  trajectory: ReplayTrajectory;
}

interface SimulationReplayProps {
  replays: ReplayCatalogEntry[];
}

const CELL_SIZE = 40;
const AGENT_SIZE = 48;
const AGENT_OFFSET = (AGENT_SIZE - CELL_SIZE) / 2;
const PLAYBACK_SPEEDS = [1, 2, 4, 8] as const;

function getShelfColors(type: string) {
  if (type === "checkout") {
    return {
      fill: "#d4f3da",
      border: "#3a8a54",
    };
  }
  if (type === "entrance") {
    return {
      fill: "#f7d4e9",
      border: "#b54487",
    };
  }
  return {
    fill: "#dfe6ff",
    border: "#4865b0",
  };
}

function getAgentStatusLabel(agent: ReplayAgent, currentStep: number): string {
  if (currentStep < 0) {
    return "Waiting at spawn";
  }
  if (agent.steps.length === 0 || currentStep >= agent.steps.length) {
    return `Finished: ${formatCompletionReason(agent.completionReason)}`;
  }
  return "Active";
}

function getTrailPoints(agent: ReplayAgent, currentStep: number) {
  if (currentStep < 0 || agent.steps.length === 0) {
    return [];
  }

  const points = [
    {
      x: agent.spawnX * CELL_SIZE + CELL_SIZE / 2,
      y: agent.spawnY * CELL_SIZE + CELL_SIZE / 2,
    },
  ];

  const visibleSteps = Math.min(currentStep + 1, agent.steps.length);
  for (let index = 0; index < visibleSteps; index += 1) {
    points.push({
      x: agent.steps[index].positionX * CELL_SIZE + CELL_SIZE / 2,
      y: agent.steps[index].positionY * CELL_SIZE + CELL_SIZE / 2,
    });
  }

  return points;
}

function ReplayBoard({
  bounds,
  trajectory,
  currentStep,
  selectedAgentId,
  onSelectAgent,
}: {
  bounds: ReplayBounds;
  trajectory: ReplayTrajectory;
  currentStep: number;
  selectedAgentId: string | null;
  onSelectAgent: (agentId: string | null) => void;
}) {
  const patternId = useId();
  const viewBox = `${bounds.minX * CELL_SIZE} ${bounds.minY * CELL_SIZE} ${bounds.width * CELL_SIZE} ${bounds.height * CELL_SIZE}`;
  const selectedAgent =
    trajectory.agents.find((agent) => agent.customerId === selectedAgentId) ?? null;
  const trailPoints = selectedAgent ? getTrailPoints(selectedAgent, currentStep) : [];

  return (
    <div
      className="w-full max-w-full overflow-hidden rounded-[28px] border border-black/10 bg-[#f6f1ea] shadow-[0_12px_50px_rgba(17,17,17,0.08)]"
      style={{
        aspectRatio: `${bounds.width} / ${bounds.height}`,
      }}
    >
      <svg
        aria-label="Retail replay board"
        className="block h-full w-full"
        viewBox={viewBox}
        preserveAspectRatio="xMidYMid meet"
        onClick={() => onSelectAgent(null)}
      >
        <defs>
          <pattern
            id={patternId}
            x="0"
            y="0"
            width={CELL_SIZE}
            height={CELL_SIZE}
            patternUnits="userSpaceOnUse"
          >
            <path
              d={`M ${CELL_SIZE} 0 L 0 0 0 ${CELL_SIZE}`}
              fill="none"
              stroke="rgba(17,17,17,0.12)"
              strokeWidth="1"
            />
          </pattern>
        </defs>

        <rect
          x={bounds.minX * CELL_SIZE}
          y={bounds.minY * CELL_SIZE}
          width={bounds.width * CELL_SIZE}
          height={bounds.height * CELL_SIZE}
          fill="#fbf8f3"
        />
        <rect
          x={bounds.minX * CELL_SIZE}
          y={bounds.minY * CELL_SIZE}
          width={bounds.width * CELL_SIZE}
          height={bounds.height * CELL_SIZE}
          fill={`url(#${patternId})`}
        />

        {trajectory.layout.shelves.map((shelf) => {
          const colors = getShelfColors(shelf.type);
          const x = shelf.x * CELL_SIZE;
          const y = shelf.y * CELL_SIZE;

          return (
            <g key={`${shelf.type}-${shelf.x}-${shelf.y}`}>
              <rect
                x={x + 4}
                y={y + 4}
                width={CELL_SIZE - 8}
                height={CELL_SIZE - 8}
                rx="10"
                fill={colors.fill}
                stroke={colors.border}
                strokeWidth="2"
              />
              {shelf.type === "checkout" ? (
                <image
                  href="/replay-assets/checkout.png"
                  x={x + 4}
                  y={y + 4}
                  width={CELL_SIZE - 8}
                  height={CELL_SIZE - 8}
                  preserveAspectRatio="xMidYMid slice"
                />
              ) : null}
            </g>
          );
        })}

        {trailPoints.length > 1 ? (
          <g aria-hidden="true">
            {trailPoints.slice(1).map((point, index) => {
              const previous = trailPoints[index];
              const alpha = 0.2 + ((index + 1) / (trailPoints.length - 1)) * 0.75;

              return (
                <g key={`trail-${index}-${previous.x}-${previous.y}-${point.x}-${point.y}`}>
                  <line
                    x1={previous.x}
                    y1={previous.y}
                    x2={point.x}
                    y2={point.y}
                    stroke={`rgba(181, 66, 120, ${alpha.toFixed(2)})`}
                    strokeWidth="4"
                    strokeLinecap="round"
                  />
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r="4"
                    fill={`rgba(181, 66, 120, ${alpha.toFixed(2)})`}
                  />
                </g>
              );
            })}
          </g>
        ) : null}

        {trajectory.agents.map((agent) => {
          const snapshot = getReplayAgentSnapshot(agent, currentStep);
          const centerX = snapshot.x * CELL_SIZE + CELL_SIZE / 2;
          const centerY = snapshot.y * CELL_SIZE + CELL_SIZE / 2;
          const isSelected = selectedAgentId === agent.customerId;

          return (
            <g
              key={agent.customerId}
              onClick={(event) => {
                event.stopPropagation();
                onSelectAgent(agent.customerId);
              }}
            >
              {snapshot.isFinished ? (
                <circle
                  cx={centerX}
                  cy={centerY}
                  r="18"
                  fill="rgba(17,17,17,0.05)"
                  stroke="rgba(17,17,17,0.18)"
                  strokeDasharray="5 4"
                />
              ) : null}

              {isSelected ? (
                <circle
                  cx={centerX}
                  cy={centerY}
                  r="24"
                  fill="rgba(124,95,214,0.08)"
                  stroke="#7c5fd6"
                  strokeWidth="3"
                />
              ) : null}

              <image
                href={getAgentSpritePath(agent.spriteName)}
                x={snapshot.x * CELL_SIZE - AGENT_OFFSET}
                y={snapshot.y * CELL_SIZE - AGENT_OFFSET}
                width={AGENT_SIZE}
                height={AGENT_SIZE}
                preserveAspectRatio="xMidYMid meet"
                opacity={snapshot.isFinished ? 0.62 : 1}
              />

              <circle cx={centerX} cy={centerY} r="24" fill="transparent" />
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function CartList({
  currency,
  items,
  emptyLabel,
}: {
  currency: string;
  items: ReplayCartItem[];
  emptyLabel: string;
}) {
  if (items.length === 0) {
    return <p className="text-[13px] leading-relaxed text-black/55">{emptyLabel}</p>;
  }

  return (
    <div className="space-y-2">
      {items.map((item, index) => (
        <div
          key={`${item.productName}-${index}`}
          className="rounded-2xl border border-black/8 bg-[#f7f3ee] px-3 py-3"
        >
          <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-black">
            {item.productName}
          </div>
          <div className="mt-1 text-[12px] text-black/55">{item.company}</div>
          <div className="mt-2 text-[12px] text-black/70">
            {formatCurrency(item.sellingPrice, currency)}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function SimulationReplay({ replays }: SimulationReplayProps) {
  const [selectedReplayId, setSelectedReplayId] = useState<string>(
    replays[0]?.id ?? "",
  );
  const [currentStep, setCurrentStep] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] =
    useState<(typeof PLAYBACK_SPEEDS)[number]>(2);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  const selectedReplay =
    replays.find((replay) => replay.id === selectedReplayId) ?? replays[0] ?? null;
  const trajectory = selectedReplay?.trajectory ?? null;
  const maxSteps = trajectory?.maxSteps ?? 0;
  const bounds = trajectory ? getReplayBounds(trajectory) : null;
  const selectedAgent =
    trajectory?.agents.find((agent) => agent.customerId === selectedAgentId) ?? null;
  const selectedSnapshot =
    selectedAgent && trajectory
      ? getReplayAgentSnapshot(selectedAgent, currentStep)
      : null;
  const hasReplayPicker = replays.length > 1;

  function selectReplay(replayId: string) {
    setSelectedReplayId(replayId);
    setCurrentStep(-1);
    setIsPlaying(false);
    setSelectedAgentId(null);
  }

  function stepBackward() {
    setIsPlaying(false);
    setCurrentStep((previousStep) => Math.max(previousStep - 1, -1));
  }

  function stepForward() {
    setIsPlaying(false);
    setCurrentStep((previousStep) => Math.min(previousStep + 1, maxSteps - 1));
  }

  function goToStart() {
    setIsPlaying(false);
    setCurrentStep(-1);
  }

  function goToEnd() {
    setIsPlaying(false);
    setCurrentStep(maxSteps > 0 ? maxSteps - 1 : -1);
  }

  function togglePlayback() {
    if (maxSteps === 0) {
      return;
    }
    if (!isPlaying && currentStep >= maxSteps - 1) {
      setCurrentStep(-1);
    }
    setIsPlaying((playing) => !playing);
  }

  const advancePlayback = useEffectEvent(() => {
    if (!trajectory || maxSteps === 0) {
      return;
    }

    if (currentStep >= maxSteps - 1) {
      setIsPlaying(false);
      return;
    }

    const nextStep = Math.min(currentStep + 1, maxSteps - 1);
    setCurrentStep(nextStep);

    if (nextStep >= maxSteps - 1) {
      setIsPlaying(false);
    }
  });

  useEffect(() => {
    if (!isPlaying || !trajectory || maxSteps === 0) {
      return;
    }

    const intervalId = window.setInterval(() => {
      advancePlayback();
    }, 1000 / playbackSpeed);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [isPlaying, maxSteps, playbackSpeed, trajectory]);

  const onKeyDown = useEffectEvent((event: KeyboardEvent) => {
    const target = event.target;
    if (
      target instanceof HTMLElement &&
      (target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable)
    ) {
      return;
    }

    if (!trajectory || maxSteps === 0) {
      return;
    }

    if (event.code === "Space") {
      event.preventDefault();
      togglePlayback();
      return;
    }

    if (event.key === "ArrowRight") {
      event.preventDefault();
      stepForward();
      return;
    }

    if (event.key === "ArrowLeft") {
      event.preventDefault();
      stepBackward();
    }
  });

  useEffect(() => {
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  if (!selectedReplay || !trajectory || !bounds) {
    return (
      <div className="rounded-[32px] border border-black/10 bg-white px-6 py-8 text-center shadow-[0_18px_60px_rgba(17,17,17,0.08)]">
        <p className="font-[family-name:var(--font-geist-pixel-square)] text-[12px] uppercase tracking-[0.18em] text-black/50">
          Replay unavailable
        </p>
      </div>
    );
  }

  const replayLabel = getReplayStepLabel(currentStep, maxSteps);
  const selectedAgentInventory = selectedSnapshot?.step?.inventory ?? [];
  const selectedAgentPurchases = selectedSnapshot?.step?.checkedOutItems ?? [];
  const selectedAgentTargets = selectedAgent?.shoppingTargets ?? [];
  const selectedUnavailableTargets = selectedAgent?.unavailableTargets ?? [];
  const selectedStatus = selectedAgent
    ? getAgentStatusLabel(selectedAgent, currentStep)
    : null;
  const sliderValue = currentStep + 1;
  const sliderMax = Math.max(0, maxSteps);

  return (
    <div className="w-full max-w-full overflow-hidden rounded-[34px] border border-black/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.95),rgba(245,241,234,0.95))] p-3 shadow-[0_20px_80px_rgba(17,17,17,0.1)] sm:p-5 lg:p-8">
      <div className="mx-auto max-w-3xl text-center">
        <p className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-[var(--accent-deep)]">
          Simulation Output
        </p>
        <h2 className="mt-3 font-[family-name:var(--font-geist-pixel-square)] text-[clamp(24px,4vw,46px)] leading-[1.08] text-[var(--ink)]">
          Real results from Gary.2 simulations.
        </h2>
        <p className="mx-auto mt-3 max-w-2xl font-[family-name:var(--font-geist-pixel-square)] text-[12px] leading-6 text-[var(--ink-mid)] sm:leading-7">
          These runs come directly from our retail simulation tests. Tap any
          shopper, scrub the timeline, and inspect routes, actions, reasoning,
          and basket state.
        </p>
      </div>

      {hasReplayPicker ? (
        <div className="mx-auto mt-5 flex w-fit max-w-full justify-center">
          <div
            role="tablist"
            aria-label="Replay layouts"
            className="inline-flex max-w-full items-center gap-2 rounded-[24px] border border-black/8 bg-white/75 p-2 shadow-[0_8px_24px_rgba(17,17,17,0.06)]"
          >
          {replays.map((replay) => {
            const isActive = replay.id === selectedReplay.id;
            return (
              <button
                key={replay.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => selectReplay(replay.id)}
                className={`min-w-[7.5rem] whitespace-nowrap rounded-[18px] border px-4 py-2.5 text-center transition sm:min-w-[8.75rem] ${
                  isActive
                    ? "border-[var(--accent-deep)] bg-[var(--accent)]/18 text-[var(--ink)] shadow-[0_8px_24px_rgba(124,95,214,0.16)]"
                    : "border-black/10 bg-white/80 text-[var(--ink-mid)] hover:border-[var(--accent-deep)]/35 hover:text-[var(--ink)]"
                }`}
              >
                <div className="font-[family-name:var(--font-geist-pixel-square)] text-[10px] sm:text-[11px]">
                  {replay.label}
                </div>
              </button>
            );
          })}
        </div>
        </div>
      ) : null}

      <div className="mt-5 grid min-w-0 gap-4 lg:mt-6 lg:gap-6 xl:grid-cols-[minmax(0,1.75fr)_minmax(320px,0.95fr)]">
        <div className="min-w-0 space-y-4 lg:space-y-5">
          <ReplayBoard
            bounds={bounds}
            trajectory={trajectory}
            currentStep={currentStep}
            selectedAgentId={selectedAgentId}
            onSelectAgent={setSelectedAgentId}
          />

          <div className="rounded-[28px] border border-black/8 bg-white/85 p-4 shadow-[0_10px_36px_rgba(17,17,17,0.08)] sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-black/45">
                  Playback
                </div>
                <div className="mt-2 font-[family-name:var(--font-geist-pixel-square)] text-[15px] text-black">
                  {replayLabel}
                </div>
              </div>

              <div className="flex flex-nowrap gap-2 overflow-x-auto pb-1 sm:flex-wrap sm:overflow-visible sm:pb-0">
                <button
                  type="button"
                  onClick={goToStart}
                  className="shrink-0 rounded-full border border-black/10 bg-[#f7f3ee] px-3 py-2 font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-black transition hover:border-[var(--accent-deep)] hover:text-[var(--accent-deep)]"
                >
                  |&lt;
                </button>
                <button
                  type="button"
                  onClick={stepBackward}
                  className="shrink-0 rounded-full border border-black/10 bg-[#f7f3ee] px-3 py-2 font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-black transition hover:border-[var(--accent-deep)] hover:text-[var(--accent-deep)]"
                >
                  &lt;
                </button>
                <button
                  type="button"
                  onClick={togglePlayback}
                  className="shrink-0 rounded-full border border-black/10 bg-black px-4 py-2 font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-white transition hover:-translate-y-0.5 hover:bg-[var(--accent-deep)]"
                >
                  {isPlaying ? "Pause" : "Play"}
                </button>
                <button
                  type="button"
                  onClick={stepForward}
                  className="shrink-0 rounded-full border border-black/10 bg-[#f7f3ee] px-3 py-2 font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-black transition hover:border-[var(--accent-deep)] hover:text-[var(--accent-deep)]"
                >
                  &gt;
                </button>
                <button
                  type="button"
                  onClick={goToEnd}
                  className="shrink-0 rounded-full border border-black/10 bg-[#f7f3ee] px-3 py-2 font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-black transition hover:border-[var(--accent-deep)] hover:text-[var(--accent-deep)]"
                >
                  &gt;|
                </button>
              </div>
            </div>

            <div className="mt-5">
              <input
                aria-label="Replay timeline"
                type="range"
                min={0}
                max={sliderMax}
                value={Math.min(sliderValue, sliderMax)}
                onChange={(event) => {
                  setIsPlaying(false);
                  setCurrentStep(Number(event.target.value) - 1);
                }}
                className="w-full accent-[var(--accent-deep)]"
              />
            </div>

            <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="text-[12px] leading-6 text-black/55">
                <span className="md:hidden">
                  Mobile: tap a shopper to inspect their replay.
                </span>
                <span className="hidden md:inline">
                  Keyboard: <span className="font-semibold text-black">space</span>{" "}
                  to play or pause,{" "}
                  <span className="font-semibold text-black">left</span> and{" "}
                  <span className="font-semibold text-black">right</span> to step.
                </span>
              </div>

              <div className="flex flex-wrap gap-2">
                {PLAYBACK_SPEEDS.map((speed) => {
                  const isActive = playbackSpeed === speed;
                  return (
                    <button
                      key={speed}
                      type="button"
                      onClick={() => setPlaybackSpeed(speed)}
                      className={`rounded-full border px-3 py-2 font-[family-name:var(--font-geist-pixel-square)] text-[11px] transition ${
                        isActive
                          ? "border-[var(--accent-deep)] bg-[var(--accent)]/20 text-[var(--ink)]"
                          : "border-black/10 bg-[#f7f3ee] text-black hover:border-[var(--accent-deep)] hover:text-[var(--accent-deep)]"
                      }`}
                    >
                      {speed}x
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        <aside className="grid min-w-0 gap-4 lg:gap-5 xl:sticky xl:top-6 xl:self-start">
          <div className="order-1 rounded-[28px] border border-black/8 bg-white/90 p-4 shadow-[0_10px_36px_rgba(17,17,17,0.08)] sm:p-5 xl:order-2">
            {selectedAgent && selectedSnapshot && selectedStatus ? (
              <div className="space-y-5">
                <div>
                  <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-black/45">
                    Shopper Replay
                  </div>
                  <div className="mt-3 font-[family-name:var(--font-geist-pixel-square)] text-[20px] text-black">
                    {selectedAgent.name}
                  </div>
                  <div className="mt-3 grid grid-cols-1 gap-2 text-[12px] leading-6 text-black/65 sm:grid-cols-2 sm:gap-3">
                    <div>Position: ({selectedSnapshot.x}, {selectedSnapshot.y})</div>
                    <div>
                      Step: {selectedSnapshot.visibleStepCount} /{" "}
                      {selectedAgent.steps.length}
                    </div>
                    <div className="sm:col-span-2">Status: {selectedStatus}</div>
                  </div>
                </div>

                {selectedSnapshot.step ? (
                  <div className="space-y-5">
                    <div>
                      <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-black/45">
                        Action
                      </div>
                      <div
                        className={`mt-3 rounded-2xl px-3 py-3 font-[family-name:var(--font-geist-pixel-square)] text-[12px] ${
                          selectedSnapshot.step.success
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-rose-50 text-rose-700"
                        }`}
                      >
                        {formatCompletionReason(selectedSnapshot.step.action)}
                        {selectedSnapshot.step.productId
                          ? ` (${selectedSnapshot.step.productId})`
                          : ""}
                        {selectedSnapshot.step.success ? "" : " [failed]"}
                      </div>
                    </div>

                    <div>
                      <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-black/45">
                        Reasoning
                      </div>
                      <p className="mt-3 text-[13px] leading-7 text-black/70">
                        {selectedSnapshot.step.rawReasoning || "No reasoning recorded."}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-black/12 bg-[#f7f3ee] px-4 py-4 text-[13px] leading-7 text-black/55">
                    Start playback or scrub the timeline to inspect decisions for
                    this shopper.
                  </div>
                )}

                <div>
                  <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-black/45">
                    Inventory
                  </div>
                  <div className="mt-3">
                    <CartList
                      currency={trajectory.layout.currency}
                      items={selectedAgentInventory}
                      emptyLabel="No items in cart."
                    />
                  </div>
                  {selectedAgentInventory.length > 0 ? (
                    <div className="mt-3 text-[12px] leading-6 text-black/70">
                      Cart total:{" "}
                      {formatCurrency(
                        selectedAgentInventory.reduce(
                          (total, item) => total + item.sellingPrice,
                          0,
                        ),
                        trajectory.layout.currency,
                      )}
                    </div>
                  ) : null}
                </div>

                <div>
                  <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-black/45">
                    Purchased
                  </div>
                  <div className="mt-3">
                    <CartList
                      currency={trajectory.layout.currency}
                      items={selectedAgentPurchases}
                      emptyLabel="No purchases recorded."
                    />
                  </div>
                  {selectedAgentPurchases.length > 0 ? (
                    <div className="mt-3 text-[12px] leading-6 text-black/70">
                      Purchased total:{" "}
                      {formatCurrency(
                        selectedAgentPurchases.reduce(
                          (total, item) => total + item.sellingPrice,
                          0,
                        ),
                        trajectory.layout.currency,
                      )}
                    </div>
                  ) : null}
                </div>

                <div>
                  <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-black/45">
                    Shopping Targets
                  </div>
                  <div className="mt-3 space-y-2">
                    {selectedAgentTargets.length > 0 ? (
                      selectedAgentTargets.map((target) => {
                        const acquired = [
                          ...selectedAgentInventory,
                          ...selectedAgentPurchases,
                        ].some((item) => item.productName === target);

                        return (
                          <div
                            key={target}
                            className={`rounded-2xl px-3 py-2 text-[12px] ${
                              acquired
                                ? "bg-emerald-50 text-emerald-700"
                                : "bg-[#f7f3ee] text-black/70"
                            }`}
                          >
                            {acquired ? "[x]" : "[ ]"} {target}
                          </div>
                        );
                      })
                    ) : (
                      <div className="rounded-2xl bg-[#f7f3ee] px-3 py-2 text-[12px] text-black/55">
                        No required shopping targets for this run.
                      </div>
                    )}
                  </div>
                </div>

                {selectedUnavailableTargets.length > 0 ? (
                  <div>
                    <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-black/45">
                      Unavailable Targets
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {selectedUnavailableTargets.map((target) => (
                        <span
                          key={target}
                          className="rounded-full border border-rose-200 bg-rose-50 px-3 py-2 text-[12px] text-rose-700"
                        >
                          {target}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-black/12 bg-[#f7f3ee] px-4 py-6 text-[13px] leading-7 text-black/55">
                Tap a shopper on the board or choose one from the list to inspect
                their route, actions, and basket.
              </div>
            )}
          </div>

          <div className="order-2 min-w-0 rounded-[28px] border border-black/8 bg-white/85 p-4 shadow-[0_10px_36px_rgba(17,17,17,0.08)] sm:p-5 xl:order-1">
            <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-black/45">
              Shoppers
            </div>
            <div className="mt-4 flex gap-2 overflow-x-auto pb-1 xl:flex-col xl:overflow-visible">
              {trajectory.agents.map((agent) => {
                const snapshot = getReplayAgentSnapshot(agent, currentStep);
                const isActive = selectedAgentId === agent.customerId;

                return (
                  <button
                    key={agent.customerId}
                    type="button"
                    onClick={() => setSelectedAgentId(agent.customerId)}
                    className={`min-w-[150px] rounded-2xl border px-3 py-3 text-left transition sm:min-w-[180px] xl:min-w-0 ${
                      isActive
                        ? "border-[var(--accent-deep)] bg-[var(--accent)]/18 shadow-[0_8px_24px_rgba(124,95,214,0.14)]"
                        : "border-black/8 bg-[#f7f3ee] hover:border-[var(--accent-deep)]/35"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-black">
                        {agent.name}
                      </div>
                      <span
                        className={`inline-flex h-2.5 w-2.5 rounded-full ${
                          snapshot.isFinished
                            ? "bg-black/30"
                            : snapshot.isWaiting
                              ? "bg-amber-400"
                              : "bg-emerald-500"
                        }`}
                      />
                    </div>
                    <div className="mt-2 text-[12px] leading-5 text-black/55">
                      {getAgentStatusLabel(agent, currentStep)}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
