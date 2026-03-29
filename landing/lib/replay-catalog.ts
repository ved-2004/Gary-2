import LayoutASimulationRun from "@/data/replay/trajectory_20260328_234023.json";
import LatestSimulationRun from "@/data/replay/trajectory_20260328_234718.json";
import { parseReplayTrajectory } from "@/lib/replay";
import type { ReplayCatalogEntry } from "@/components/SimulationReplay";

const layoutASimulationRun = parseReplayTrajectory(LayoutASimulationRun);
const latestSimulationRun = parseReplayTrajectory(LatestSimulationRun);

export const replayCatalog: ReplayCatalogEntry[] = [
  {
    id: "layout-a",
    label: "Layout A",
    trajectory: layoutASimulationRun,
  },
  {
    id: "layout-b",
    label: "Layout B",
    trajectory: latestSimulationRun,
  },
];
