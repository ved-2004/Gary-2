"use client";

import dynamic from "next/dynamic";
import type { ReplayCatalogEntry } from "@/components/SimulationReplay";

const SimulationReplay = dynamic(() => import("@/components/SimulationReplay"), {
  ssr: false,
});

export default function SimulationReplayClient({
  replays,
}: {
  replays: ReplayCatalogEntry[];
}) {
  return <SimulationReplay replays={replays} />;
}
