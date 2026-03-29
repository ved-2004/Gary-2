import type { Metadata } from "next";
import Link from "next/link";
import SimulationReplayClient from "@/components/SimulationReplayClient";
import { replayCatalog } from "@/lib/replay-catalog";

export const metadata: Metadata = {
  title: "Replay | Gary.2",
  description:
    "Interactive retail simulation replays with step controls, shopper selection, and basket detail.",
};

export default function ReplayPage() {
  return (
    <main className="ld min-h-screen">
      <div className="mx-auto max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-[family-name:var(--font-geist-pixel-square)] text-[11px] uppercase tracking-[0.18em] text-[var(--accent-deep,#7c5fd6)]">
              Gary.2 Replay
            </p>
            <h1 className="mt-3 font-[family-name:var(--font-geist-pixel-square)] text-[clamp(30px,4vw,52px)] leading-[1.05] text-[var(--ink,#111)]">
              Shopper runs, frame by frame.
            </h1>
          </div>

          <Link
            href="/"
            className="inline-flex w-fit items-center rounded-full border border-black/10 bg-white px-4 py-3 font-[family-name:var(--font-geist-pixel-square)] text-[11px] text-[var(--ink,#111)] transition hover:-translate-y-0.5 hover:border-[var(--accent-deep,#7c5fd6)] hover:text-[var(--accent-deep,#7c5fd6)]"
          >
            Back home
          </Link>
        </div>

        <SimulationReplayClient replays={replayCatalog} />
      </div>
    </main>
  );
}
