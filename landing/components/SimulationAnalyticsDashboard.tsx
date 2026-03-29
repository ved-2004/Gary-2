"use client";

import { useMemo } from "react";
import { formatCurrency } from "@/lib/replay";
import {
  buildReplayAnalyticsStudy,
  type PairedAgentComparison,
  type PermutationStatus,
  type ReplayAnalyticsStudy,
  type SimulationResultsDataset,
} from "@/lib/simulation-results";

interface AnalyticsReplayEntry {
  id: string;
  label: string;
  results?: SimulationResultsDataset | null;
}

interface SimulationAnalyticsDashboardProps {
  replays: AnalyticsReplayEntry[];
  currency: string;
}

const LAYOUT_A_COLOR = "#111111";
const LAYOUT_B_COLOR = "#7c5fd6";

function formatSignedPercent(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function formatSignedCurrency(value: number, currency: string) {
  const formatted = formatCurrency(Math.abs(value), currency);
  if (value > 0) {
    return `+${formatted}`;
  }
  if (value < 0) {
    return `-${formatted}`;
  }
  return formatted;
}

function formatSignedSteps(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)} steps`;
}

function formatSignedPoints(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)} pts`;
}

function formatPValue(value: number) {
  return `p = ${value.toFixed(4)}`;
}

function getDeltaTone(
  delta: number,
  higherIsBetter: boolean,
) {
  if (Math.abs(delta) < Number.EPSILON) {
    return {
      badge: "border-black/8 bg-black/[0.04] text-black/55",
      label: "No change",
    };
  }

  const improved = higherIsBetter ? delta > 0 : delta < 0;
  return improved
    ? {
        badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
        label: "Improved",
      }
    : {
        badge: "border-rose-200 bg-rose-50 text-rose-700",
        label: "Dropped",
      };
}

function getStatusTone(status: PermutationStatus) {
  if (status === "significant") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (status === "directional") {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }
  return "border-black/8 bg-black/[0.04] text-black/55";
}

function getStatusLabel(status: PermutationStatus) {
  if (status === "significant") {
    return "Significant";
  }
  if (status === "directional") {
    return "Directional";
  }
  return "Not significant";
}

function MetricCard({
  title,
  detail,
  layoutALabel,
  layoutAValue,
  layoutBLabel,
  layoutBValue,
  deltaLabel,
  deltaValue,
  higherIsBetter,
}: {
  title: string;
  detail: string;
  layoutALabel: string;
  layoutAValue: string;
  layoutBLabel: string;
  layoutBValue: string;
  deltaLabel: string;
  deltaValue: number;
  higherIsBetter: boolean;
}) {
  const tone = getDeltaTone(deltaValue, higherIsBetter);

  return (
    <div className="rounded-[24px] border border-black/8 bg-white/88 p-4 shadow-[0_10px_28px_rgba(17,17,17,0.06)] sm:p-5">
      <div className="font-[family-name:var(--font-geist-pixel-square)] text-[10px] uppercase tracking-[0.18em] text-black/45">
        {title}
      </div>
      <div className="mt-2 text-[12px] leading-6 text-black/55">{detail}</div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-2xl border border-black/8 bg-[#f7f3ee] px-3 py-3">
          <div className="font-[family-name:var(--font-geist-pixel-square)] text-[10px] text-black/45">
            {layoutALabel}
          </div>
          <div className="mt-2 text-[18px] font-semibold text-black">{layoutAValue}</div>
        </div>
        <div className="rounded-2xl border border-[rgba(124,95,214,0.16)] bg-[rgba(124,95,214,0.08)] px-3 py-3">
          <div className="font-[family-name:var(--font-geist-pixel-square)] text-[10px] text-[var(--accent-deep)]">
            {layoutBLabel}
          </div>
          <div className="mt-2 text-[18px] font-semibold text-black">{layoutBValue}</div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <div className="text-[12px] leading-6 text-black/55">{deltaLabel}</div>
        <div className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold ${tone.badge}`}>
          {tone.label}
        </div>
      </div>
    </div>
  );
}

function SpendVsStepsChart({
  study,
  currency,
}: {
  study: ReplayAnalyticsStudy;
  currency: string;
}) {
  const width = 560;
  const height = 320;
  const paddingLeft = 54;
  const paddingRight = 20;
  const paddingTop = 22;
  const paddingBottom = 40;
  const innerWidth = width - paddingLeft - paddingRight;
  const innerHeight = height - paddingTop - paddingBottom;
  const maxSteps = Math.max(
    ...study.spendVsStepsPoints.map((point) => point.simulationSteps),
    1,
  );
  const maxSpend = Math.max(...study.spendVsStepsPoints.map((point) => point.spend), 1);
  const tickCount = 4;

  return (
    <div className="rounded-[24px] border border-black/8 bg-white/88 p-4 shadow-[0_10px_28px_rgba(17,17,17,0.06)] sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="font-[family-name:var(--font-geist-pixel-square)] text-[10px] uppercase tracking-[0.18em] text-black/45">
            Spend vs Simulation Steps
          </div>
          <div className="mt-2 text-[13px] leading-6 text-black/60">
            Each point is one shopper run. More time on floor does not guarantee
            higher checkout.
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-[11px] text-black/55">
          <div className="inline-flex items-center gap-2">
            <span
              className="inline-flex h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: LAYOUT_A_COLOR }}
            />
            {study.armA.label}
          </div>
          <div className="inline-flex items-center gap-2">
            <span
              className="inline-flex h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: LAYOUT_B_COLOR }}
            />
            {study.armB.label}
          </div>
        </div>
      </div>

      <div className="mt-5 w-full overflow-hidden">
        <svg
          className="block h-auto w-full"
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label="Scatter plot of shopper spend against simulation steps"
        >
          <rect x="0" y="0" width={width} height={height} rx="20" fill="#fbf8f3" />

          {Array.from({ length: tickCount + 1 }, (_, index) => {
            const ratio = index / tickCount;
            const y = paddingTop + innerHeight - ratio * innerHeight;
            const spendValue = (maxSpend * ratio).toFixed(0);
            return (
              <g key={`spend-grid-${index}`}>
                <line
                  x1={paddingLeft}
                  x2={width - paddingRight}
                  y1={y}
                  y2={y}
                  stroke="rgba(17,17,17,0.08)"
                  strokeDasharray="4 6"
                />
                <text
                  x={paddingLeft - 8}
                  y={y + 4}
                  textAnchor="end"
                  fill="rgba(17,17,17,0.48)"
                  fontSize="10"
                  fontFamily="var(--font-geist-pixel-square)"
                >
                  {formatCurrency(Number(spendValue), currency)}
                </text>
              </g>
            );
          })}

          {Array.from({ length: tickCount + 1 }, (_, index) => {
            const ratio = index / tickCount;
            const x = paddingLeft + ratio * innerWidth;
            return (
              <g key={`steps-grid-${index}`}>
                <line
                  x1={x}
                  x2={x}
                  y1={paddingTop}
                  y2={height - paddingBottom}
                  stroke="rgba(17,17,17,0.05)"
                />
                <text
                  x={x}
                  y={height - 14}
                  textAnchor="middle"
                  fill="rgba(17,17,17,0.48)"
                  fontSize="10"
                  fontFamily="var(--font-geist-pixel-square)"
                >
                  {Math.round(maxSteps * ratio)}
                </text>
              </g>
            );
          })}

          <line
            x1={paddingLeft}
            x2={paddingLeft}
            y1={paddingTop}
            y2={height - paddingBottom}
            stroke="rgba(17,17,17,0.18)"
          />
          <line
            x1={paddingLeft}
            x2={width - paddingRight}
            y1={height - paddingBottom}
            y2={height - paddingBottom}
            stroke="rgba(17,17,17,0.18)"
          />

          {study.spendVsStepsPoints.map((point) => {
            const x = paddingLeft + (point.simulationSteps / maxSteps) * innerWidth;
            const y = paddingTop + innerHeight - (point.spend / maxSpend) * innerHeight;
            const fill = point.layoutId === study.armA.id ? LAYOUT_A_COLOR : LAYOUT_B_COLOR;

            return (
              <circle
                key={`${point.layoutId}-${point.customerId}`}
                cx={x}
                cy={y}
                r="5.5"
                fill={fill}
                fillOpacity="0.82"
                stroke="rgba(255,255,255,0.92)"
                strokeWidth="1.5"
              >
                <title>
                  {`${point.name} • ${point.layoutLabel} • ${point.simulationSteps} steps • ${formatCurrency(point.spend, currency)}`}
                </title>
              </circle>
            );
          })}

          <text
            x={width / 2}
            y={height - 2}
            textAnchor="middle"
            fill="rgba(17,17,17,0.56)"
            fontSize="11"
            fontFamily="var(--font-geist-pixel-square)"
          >
            Simulation steps
          </text>
          <text
            x="16"
            y={paddingTop + innerHeight / 2}
            textAnchor="middle"
            fill="rgba(17,17,17,0.56)"
            fontSize="11"
            fontFamily="var(--font-geist-pixel-square)"
            transform={`rotate(-90 16 ${paddingTop + innerHeight / 2})`}
          >
            Spend
          </text>
        </svg>
      </div>
    </div>
  );
}

function SpendDeltaChart({
  pairedComparisons,
  currency,
  lowerSpendInB,
  higherSpendInB,
  sameSpend,
}: {
  pairedComparisons: PairedAgentComparison[];
  currency: string;
  lowerSpendInB: number;
  higherSpendInB: number;
  sameSpend: number;
}) {
  const width = 560;
  const height = 280;
  const paddingLeft = 30;
  const paddingRight = 20;
  const paddingTop = 18;
  const paddingBottom = 34;
  const innerWidth = width - paddingLeft - paddingRight;
  const midline = height / 2 + 6;
  const availableHalfHeight = (height - paddingTop - paddingBottom) / 2 - 10;
  const maxAbsDiff = Math.max(
    ...pairedComparisons.map((comparison) => Math.abs(comparison.spendDiff)),
    1,
  );
  const gap = 8;
  const barWidth =
    (innerWidth - gap * Math.max(pairedComparisons.length - 1, 0)) /
    Math.max(pairedComparisons.length, 1);

  return (
    <div className="rounded-[24px] border border-black/8 bg-white/88 p-4 shadow-[0_10px_28px_rgba(17,17,17,0.06)] sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="font-[family-name:var(--font-geist-pixel-square)] text-[10px] uppercase tracking-[0.18em] text-black/45">
            Per-Shopper Spend Delta
          </div>
          <div className="mt-2 text-[13px] leading-6 text-black/60">
            Same 15 shoppers, sorted by checkout change from Layout B minus Layout A.
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[11px] text-black/55">
          <span className="rounded-full border border-rose-200 bg-rose-50 px-3 py-1.5 text-rose-700">
            {lowerSpendInB} lower in B
          </span>
          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-emerald-700">
            {higherSpendInB} higher in B
          </span>
          <span className="rounded-full border border-black/8 bg-black/[0.04] px-3 py-1.5">
            {sameSpend} same
          </span>
        </div>
      </div>

      <div className="mt-5 w-full overflow-hidden">
        <svg
          className="block h-auto w-full"
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label="Bar chart of shopper spend differences between layout B and layout A"
        >
          <rect x="0" y="0" width={width} height={height} rx="20" fill="#fbf8f3" />
          <line
            x1={paddingLeft}
            x2={width - paddingRight}
            y1={midline}
            y2={midline}
            stroke="rgba(17,17,17,0.16)"
            strokeWidth="1.5"
          />
          <text
            x={paddingLeft}
            y={midline - availableHalfHeight - 6}
            fill="rgba(17,17,17,0.48)"
            fontSize="10"
            fontFamily="var(--font-geist-pixel-square)"
          >
            Higher in B
          </text>
          <text
            x={paddingLeft}
            y={midline + availableHalfHeight + 18}
            fill="rgba(17,17,17,0.48)"
            fontSize="10"
            fontFamily="var(--font-geist-pixel-square)"
          >
            Lower in B
          </text>

          {pairedComparisons.map((comparison, index) => {
            const magnitude = Math.abs(comparison.spendDiff);
            const scaledHeight = (magnitude / maxAbsDiff) * availableHalfHeight;
            const x = paddingLeft + index * (barWidth + gap);
            const y =
              comparison.spendDiff >= 0 ? midline - scaledHeight : midline;
            const fill =
              comparison.spendDiff > 0
                ? LAYOUT_B_COLOR
                : comparison.spendDiff < 0
                  ? "#d16464"
                  : "rgba(17,17,17,0.28)";

            return (
              <rect
                key={comparison.customerId}
                x={x}
                y={y}
                width={barWidth}
                height={Math.max(scaledHeight, 2)}
                rx="4"
                fill={fill}
                opacity="0.86"
              >
                <title>
                  {`${comparison.name}: ${formatCurrency(comparison.spendB, currency)} vs ${formatCurrency(comparison.spendA, currency)} (${formatCurrency(comparison.spendDiff, currency)})`}
                </title>
              </rect>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

function StatsPanel({
  study,
  currency,
}: {
  study: ReplayAnalyticsStudy;
  currency: string;
}) {
  const statRows = [
    {
      label: "Checkout spend",
      effect: formatSignedCurrency(study.tests.spend.meanDifference, currency),
      detail: "Mean shopper change in Layout B minus Layout A",
      result: study.tests.spend,
    },
    {
      label: "Simulation steps",
      effect: formatSignedSteps(study.tests.simulationSteps.meanDifference),
      detail: "Lower means faster trips through the store",
      result: study.tests.simulationSteps,
    },
    {
      label: "Fulfillment rate",
      effect: formatSignedPoints(study.tests.fulfillment.meanDifference * 100),
      detail: "Average fulfilled available targets",
      result: study.tests.fulfillment,
    },
  ];

  return (
    <div className="rounded-[24px] border border-black/8 bg-white/88 p-4 shadow-[0_10px_28px_rgba(17,17,17,0.06)] sm:p-5">
      <div className="font-[family-name:var(--font-geist-pixel-square)] text-[10px] uppercase tracking-[0.18em] text-black/45">
        Paired Stats
      </div>
      <div className="mt-2 text-[13px] leading-6 text-black/60">
        Exact paired permutation tests on the same {study.pairedComparisons.length}{" "}
        shoppers in both layouts.
      </div>

      <div className="mt-5 space-y-3">
        {statRows.map((row) => (
          <div
            key={row.label}
            className="rounded-2xl border border-black/8 bg-[#f7f3ee] px-3 py-3"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-black">
                  {row.label}
                </div>
                <div className="mt-2 text-[13px] font-semibold text-black">{row.effect}</div>
                <div className="mt-1 text-[12px] leading-6 text-black/55">{row.detail}</div>
              </div>
              <div
                className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold ${getStatusTone(row.result.status)}`}
              >
                {getStatusLabel(row.result.status)}
              </div>
            </div>
            <div className="mt-3 text-[12px] text-black/55">
              {formatPValue(row.result.pValue)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function SimulationAnalyticsDashboard({
  replays,
  currency,
}: SimulationAnalyticsDashboardProps) {
  const study = useMemo(() => buildReplayAnalyticsStudy(replays), [replays]);

  if (!study) {
    return null;
  }

  return (
    <section className="mt-6 space-y-4 sm:mt-8 sm:space-y-5">
      <div className="rounded-[28px] border border-[rgba(124,95,214,0.12)] bg-[linear-gradient(135deg,rgba(255,255,255,0.94),rgba(124,95,214,0.08))] p-5 shadow-[0_14px_42px_rgba(17,17,17,0.08)] sm:p-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-black/8 bg-white/72 px-3 py-1.5 font-[family-name:var(--font-geist-pixel-square)] text-[10px] uppercase tracking-[0.16em] text-black/55">
            A/B Readout
          </span>
          <span className="rounded-full border border-[rgba(124,95,214,0.16)] bg-[rgba(124,95,214,0.1)] px-3 py-1.5 font-[family-name:var(--font-geist-pixel-square)] text-[10px] uppercase tracking-[0.16em] text-[var(--accent-deep)]">
            Popup-store test
          </span>
        </div>

        <h3 className="mt-4 font-[family-name:var(--font-geist-pixel-square)] text-[clamp(22px,3vw,34px)] leading-[1.12] text-[var(--ink)]">
          Moving demand forward sped shoppers up, but checkout dollars fell.
        </h3>

        <p className="mt-4 max-w-4xl text-[14px] leading-7 text-black/66">
          In {study.armA.label}, {study.armA.summary.shoppersWithUnavailableTargets} of{" "}
          {study.armA.summary.agentCount} shoppers still had at least one unavailable
          target on their list. We used {study.armB.label} as the popup-store
          experiment and pulled those demand pockets closer to the front. On the
          same shopper set, average trips dropped {Math.abs(study.narrative.stepsDeltaPercent).toFixed(1)}%, but total checkout revenue also fell {Math.abs(study.narrative.revenueDeltaPercent).toFixed(1)}% and fulfillment slipped {Math.abs(study.narrative.fulfillmentDeltaPoints).toFixed(1)} points.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Total Checkout Revenue"
          detail="Total dollars captured at checkout across the full layout run."
          layoutALabel={study.armA.label}
          layoutAValue={formatCurrency(study.armA.summary.totalCheckoutRevenue, currency)}
          layoutBLabel={study.armB.label}
          layoutBValue={formatCurrency(study.armB.summary.totalCheckoutRevenue, currency)}
          deltaLabel={`B vs A ${formatSignedPercent(study.narrative.revenueDeltaPercent)}`}
          deltaValue={study.narrative.revenueDeltaPercent}
          higherIsBetter
        />
        <MetricCard
          title="Average Spend"
          detail="Checkout dollars per shopper."
          layoutALabel={study.armA.label}
          layoutAValue={formatCurrency(study.armA.summary.averageSpend, currency)}
          layoutBLabel={study.armB.label}
          layoutBValue={formatCurrency(study.armB.summary.averageSpend, currency)}
          deltaLabel={`B vs A ${formatSignedCurrency(study.armB.summary.averageSpend - study.armA.summary.averageSpend, currency)}`}
          deltaValue={study.armB.summary.averageSpend - study.armA.summary.averageSpend}
          higherIsBetter
        />
        <MetricCard
          title="Average Simulation Steps"
          detail="Used here as the dwell-time proxy."
          layoutALabel={study.armA.label}
          layoutAValue={study.armA.summary.averageSimulationSteps.toFixed(1)}
          layoutBLabel={study.armB.label}
          layoutBValue={study.armB.summary.averageSimulationSteps.toFixed(1)}
          deltaLabel={`B vs A ${formatSignedSteps(study.armB.summary.averageSimulationSteps - study.armA.summary.averageSimulationSteps)}`}
          deltaValue={study.armB.summary.averageSimulationSteps - study.armA.summary.averageSimulationSteps}
          higherIsBetter={false}
        />
        <MetricCard
          title="Fulfillment Rate"
          detail="Average share of available targets each shopper actually fulfilled."
          layoutALabel={study.armA.label}
          layoutAValue={`${(study.armA.summary.averageFulfillmentRate * 100).toFixed(1)}%`}
          layoutBLabel={study.armB.label}
          layoutBValue={`${(study.armB.summary.averageFulfillmentRate * 100).toFixed(1)}%`}
          deltaLabel={`B vs A ${formatSignedPoints(study.narrative.fulfillmentDeltaPoints)}`}
          deltaValue={study.narrative.fulfillmentDeltaPoints}
          higherIsBetter
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.85fr)]">
        <div className="grid gap-4">
          <SpendVsStepsChart study={study} currency={currency} />
          <SpendDeltaChart
            pairedComparisons={study.pairedComparisons}
            currency={currency}
            lowerSpendInB={study.shopperOutcomeCounts.lowerSpendInB}
            higherSpendInB={study.shopperOutcomeCounts.higherSpendInB}
            sameSpend={study.shopperOutcomeCounts.sameSpend}
          />
        </div>
        <StatsPanel study={study} currency={currency} />
      </div>
    </section>
  );
}
