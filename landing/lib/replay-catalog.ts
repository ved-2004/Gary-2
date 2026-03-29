import LatestSimulationRun from "@/data/replay/trajectory_20260328_234718.json";
import { parseReplayTrajectory } from "@/lib/replay";
import type { ReplayCatalogEntry } from "@/components/SimulationReplay";

const latestSimulationRun = parseReplayTrajectory(LatestSimulationRun);

export const replayCatalog: ReplayCatalogEntry[] = [
  {
    id: "latest-demo",
    label: "Latest Demo",
    trajectory: latestSimulationRun,
  },
];
