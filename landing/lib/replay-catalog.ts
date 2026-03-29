import LayoutASimulationRun from "@/data/replay/trajectory_20260329_141807.json";
import LayoutBSimulationRun from "@/data/replay/trajectory_20260329_143750.json";
import LayoutAResults from "@/data/analytics/results-1.json";
import LayoutBResults from "@/data/analytics/results-2.json";
import { parseReplayTrajectory } from "@/lib/replay";
import { parseSimulationResults } from "@/lib/simulation-results";
import type { ReplayCatalogEntry } from "@/components/SimulationReplay";

const layoutASimulationRun = parseReplayTrajectory(LayoutASimulationRun);
const layoutBSimulationRun = parseReplayTrajectory(LayoutBSimulationRun);
const layoutAResults = parseSimulationResults(LayoutAResults);
const layoutBResults = parseSimulationResults(LayoutBResults);

export const replayCatalog: ReplayCatalogEntry[] = [
  {
    id: "layout-a",
    label: "Layout A",
    trajectory: layoutASimulationRun,
    results: layoutAResults,
  },
  {
    id: "layout-b",
    label: "Layout B",
    trajectory: layoutBSimulationRun,
    results: layoutBResults,
  },
];
