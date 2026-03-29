export interface SimulationPurchasedItem {
  productId: string;
  productName: string;
  productType: string;
  company: string;
  sellingPrice: number;
  procurementCost: number;
  discountPercent: number;
  marginPercent: number;
  shelfX: number;
  shelfY: number;
}

export interface SimulationAgentOutcome {
  name: string;
  state: string;
  currentPositionX: number;
  currentPositionY: number;
  itemsPurchased: SimulationPurchasedItem[];
  spend: number;
  customerId: string;
  completionReason: string;
  iterationCount: number;
  maxIterations: number;
  uniquePositionsVisited: number;
  shoppingTargets: string[];
  unavailableTargets: string[];
  remainingTargets: string[];
  failureCount: number;
  successfulActionCount: number;
  lastError: string;
}

export interface SimulationResultsDataset {
  agents: SimulationAgentOutcome[];
}

export interface SimulationSummary {
  totalCheckoutRevenue: number;
  averageSpend: number;
  averageSimulationSteps: number;
  averageUniquePositionsVisited: number;
  averageFailures: number;
  averagePurchasedItems: number;
  averageTargets: number;
  averageAvailableTargets: number;
  averageRemainingTargets: number;
  averageFulfilledTargets: number;
  averageFulfillmentRate: number;
  shoppersWithUnavailableTargets: number;
  checkedOutCount: number;
  agentCount: number;
}

export interface LayoutAnalyticsArm {
  id: string;
  label: string;
  results: SimulationResultsDataset;
  summary: SimulationSummary;
}

export interface SpendVsStepsPoint {
  customerId: string;
  name: string;
  layoutId: string;
  layoutLabel: string;
  spend: number;
  simulationSteps: number;
}

export interface PairedAgentComparison {
  customerId: string;
  name: string;
  spendA: number;
  spendB: number;
  spendDiff: number;
  simulationStepsA: number;
  simulationStepsB: number;
  simulationStepsDiff: number;
  fulfillmentRateA: number;
  fulfillmentRateB: number;
  fulfillmentRateDiff: number;
  unavailableA: number;
  unavailableB: number;
  unavailableDiff: number;
}

export type PermutationStatus = "significant" | "directional" | "not_significant";

export interface PairedPermutationTestResult {
  meanDifference: number;
  pValue: number;
  status: PermutationStatus;
}

export interface ReplayAnalyticsStudy {
  armA: LayoutAnalyticsArm;
  armB: LayoutAnalyticsArm;
  spendVsStepsPoints: SpendVsStepsPoint[];
  pairedComparisons: PairedAgentComparison[];
  tests: {
    spend: PairedPermutationTestResult;
    simulationSteps: PairedPermutationTestResult;
    fulfillment: PairedPermutationTestResult;
  };
  shopperOutcomeCounts: {
    lowerSpendInB: number;
    higherSpendInB: number;
    sameSpend: number;
    lowerStepsInB: number;
    higherStepsInB: number;
    sameSteps: number;
  };
  narrative: {
    revenueDeltaPercent: number;
    stepsDeltaPercent: number;
    fulfillmentDeltaPoints: number;
  };
}

function expectRecord(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${label} must be an object.`);
  }
  return value as Record<string, unknown>;
}

function expectArray(value: unknown, label: string): unknown[] {
  if (!Array.isArray(value)) {
    throw new Error(`${label} must be an array.`);
  }
  return value;
}

function expectString(value: unknown, label: string): string {
  if (typeof value !== "string") {
    throw new Error(`${label} must be a string.`);
  }
  return value;
}

function expectNumber(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`${label} must be a finite number.`);
  }
  return value;
}

function expectStringArray(value: unknown, label: string): string[] {
  return expectArray(value, label).map((entry, index) =>
    expectString(entry, `${label}[${index}]`),
  );
}

function parsePurchasedItem(
  rawValue: unknown,
  label: string,
): SimulationPurchasedItem {
  const item = expectRecord(rawValue, label);

  return {
    productId: expectString(item.product_id, `${label}.product_id`),
    productName: expectString(item.product_name, `${label}.product_name`),
    productType: expectString(item.product_type, `${label}.product_type`),
    company: expectString(item.company, `${label}.company`),
    sellingPrice: expectNumber(item.selling_price, `${label}.selling_price`),
    procurementCost: expectNumber(
      item.procurement_cost,
      `${label}.procurement_cost`,
    ),
    discountPercent: expectNumber(
      item.discount_percent,
      `${label}.discount_percent`,
    ),
    marginPercent: expectNumber(item.margin_percent, `${label}.margin_percent`),
    shelfX: expectNumber(item.shelf_x, `${label}.shelf_x`),
    shelfY: expectNumber(item.shelf_y, `${label}.shelf_y`),
  };
}

function parseAgentOutcome(
  rawValue: unknown,
  label: string,
): SimulationAgentOutcome {
  const agent = expectRecord(rawValue, label);
  const currentPosition = expectRecord(
    agent.current_position,
    `${label}.current_position`,
  );

  return {
    name: expectString(agent.name, `${label}.name`),
    state: expectString(agent.state, `${label}.state`),
    currentPositionX: expectNumber(currentPosition.x, `${label}.current_position.x`),
    currentPositionY: expectNumber(currentPosition.y, `${label}.current_position.y`),
    itemsPurchased: expectArray(
      agent.items_purchased ?? [],
      `${label}.items_purchased`,
    ).map((item, index) =>
      parsePurchasedItem(item, `${label}.items_purchased[${index}]`),
    ),
    spend: expectNumber(agent.spend, `${label}.spend`),
    customerId: expectString(agent.customer_id, `${label}.customer_id`),
    completionReason: expectString(
      agent.completion_reason,
      `${label}.completion_reason`,
    ),
    iterationCount: expectNumber(agent.iteration_count, `${label}.iteration_count`),
    maxIterations: expectNumber(agent.max_iterations, `${label}.max_iterations`),
    uniquePositionsVisited: expectNumber(
      agent.unique_positions_visited,
      `${label}.unique_positions_visited`,
    ),
    shoppingTargets: expectStringArray(
      agent.shopping_targets ?? [],
      `${label}.shopping_targets`,
    ),
    unavailableTargets: expectStringArray(
      agent.unavailable_targets ?? [],
      `${label}.unavailable_targets`,
    ),
    remainingTargets: expectStringArray(
      agent.remaining_targets ?? [],
      `${label}.remaining_targets`,
    ),
    failureCount: expectNumber(agent.failure_count, `${label}.failure_count`),
    successfulActionCount: expectNumber(
      agent.successful_action_count,
      `${label}.successful_action_count`,
    ),
    lastError:
      typeof agent.last_error === "string"
        ? agent.last_error
        : "",
  };
}

export function parseSimulationResults(rawValue: unknown): SimulationResultsDataset {
  const raw = expectRecord(rawValue, "Simulation results");

  return {
    agents: expectArray(raw.agents ?? [], "Simulation results.agents").map(
      (agent, index) =>
        parseAgentOutcome(agent, `Simulation results.agents[${index}]`),
    ),
  };
}

function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function getPercentChange(fromValue: number, toValue: number): number {
  if (fromValue === 0) {
    return 0;
  }
  return ((toValue - fromValue) / fromValue) * 100;
}

export function getFulfillmentMetrics(agent: SimulationAgentOutcome) {
  const availableTargetCount = Math.max(
    agent.shoppingTargets.length - agent.unavailableTargets.length,
    0,
  );
  const fulfilledTargetCount = Math.max(
    availableTargetCount - agent.remainingTargets.length,
    0,
  );

  return {
    availableTargetCount,
    fulfilledTargetCount,
    fulfillmentRate:
      availableTargetCount > 0
        ? fulfilledTargetCount / availableTargetCount
        : 0,
  };
}

export function getSimulationSummary(
  results: SimulationResultsDataset,
): SimulationSummary {
  const fulfillmentRows = results.agents.map((agent) => getFulfillmentMetrics(agent));

  return {
    totalCheckoutRevenue: results.agents.reduce(
      (sum, agent) => sum + agent.spend,
      0,
    ),
    averageSpend: average(results.agents.map((agent) => agent.spend)),
    averageSimulationSteps: average(
      results.agents.map((agent) => agent.iterationCount),
    ),
    averageUniquePositionsVisited: average(
      results.agents.map((agent) => agent.uniquePositionsVisited),
    ),
    averageFailures: average(results.agents.map((agent) => agent.failureCount)),
    averagePurchasedItems: average(
      results.agents.map((agent) => agent.itemsPurchased.length),
    ),
    averageTargets: average(
      results.agents.map((agent) => agent.shoppingTargets.length),
    ),
    averageAvailableTargets: average(
      fulfillmentRows.map((row) => row.availableTargetCount),
    ),
    averageRemainingTargets: average(
      results.agents.map((agent) => agent.remainingTargets.length),
    ),
    averageFulfilledTargets: average(
      fulfillmentRows.map((row) => row.fulfilledTargetCount),
    ),
    averageFulfillmentRate: average(
      fulfillmentRows.map((row) => row.fulfillmentRate),
    ),
    shoppersWithUnavailableTargets: results.agents.filter(
      (agent) => agent.unavailableTargets.length > 0,
    ).length,
    checkedOutCount: results.agents.filter(
      (agent) => agent.completionReason === "checked_out",
    ).length,
    agentCount: results.agents.length,
  };
}

function getPermutationStatus(pValue: number): PermutationStatus {
  if (pValue < 0.05) {
    return "significant";
  }
  if (pValue < 0.15) {
    return "directional";
  }
  return "not_significant";
}

function exactPairedPermutationPValue(differences: number[]): number {
  if (differences.length === 0) {
    return 1;
  }

  const magnitudes = differences.map((value) => Math.abs(value));
  const observed = Math.abs(average(differences));
  const totalPermutations = 1 << differences.length;
  let extremeCount = 0;

  for (let mask = 0; mask < totalPermutations; mask += 1) {
    let sum = 0;

    for (let index = 0; index < magnitudes.length; index += 1) {
      const sign = (mask & (1 << index)) === 0 ? -1 : 1;
      sum += sign * magnitudes[index];
    }

    if (Math.abs(sum / magnitudes.length) >= observed - Number.EPSILON) {
      extremeCount += 1;
    }
  }

  return extremeCount / totalPermutations;
}

function buildPermutationResult(
  differences: number[],
): PairedPermutationTestResult {
  const meanDifference = average(differences);
  const pValue = exactPairedPermutationPValue(differences);

  return {
    meanDifference,
    pValue,
    status: getPermutationStatus(pValue),
  };
}

export function buildReplayAnalyticsStudy(
  arms: Array<{
    id: string;
    label: string;
    results?: SimulationResultsDataset | null;
  }>,
): ReplayAnalyticsStudy | null {
  const comparableArms = arms.filter(
    (arm): arm is { id: string; label: string; results: SimulationResultsDataset } =>
      arm.results != null,
  );

  if (comparableArms.length < 2) {
    return null;
  }

  const [armAInput, armBInput] = comparableArms;
  const armA: LayoutAnalyticsArm = {
    id: armAInput.id,
    label: armAInput.label,
    results: armAInput.results,
    summary: getSimulationSummary(armAInput.results),
  };
  const armB: LayoutAnalyticsArm = {
    id: armBInput.id,
    label: armBInput.label,
    results: armBInput.results,
    summary: getSimulationSummary(armBInput.results),
  };

  const byCustomerA = new Map(
    armA.results.agents.map((agent) => [agent.customerId, agent] as const),
  );
  const byCustomerB = new Map(
    armB.results.agents.map((agent) => [agent.customerId, agent] as const),
  );

  const sharedCustomerIds = armA.results.agents
    .map((agent) => agent.customerId)
    .filter((customerId) => byCustomerB.has(customerId));

  if (sharedCustomerIds.length < 2) {
    return null;
  }

  const pairedComparisons = sharedCustomerIds
    .map((customerId) => {
      const agentA = byCustomerA.get(customerId)!;
      const agentB = byCustomerB.get(customerId)!;
      const fulfillmentA = getFulfillmentMetrics(agentA).fulfillmentRate;
      const fulfillmentB = getFulfillmentMetrics(agentB).fulfillmentRate;

      return {
        customerId,
        name: agentA.name,
        spendA: agentA.spend,
        spendB: agentB.spend,
        spendDiff: agentB.spend - agentA.spend,
        simulationStepsA: agentA.iterationCount,
        simulationStepsB: agentB.iterationCount,
        simulationStepsDiff: agentB.iterationCount - agentA.iterationCount,
        fulfillmentRateA: fulfillmentA,
        fulfillmentRateB: fulfillmentB,
        fulfillmentRateDiff: fulfillmentB - fulfillmentA,
        unavailableA: agentA.unavailableTargets.length,
        unavailableB: agentB.unavailableTargets.length,
        unavailableDiff:
          agentB.unavailableTargets.length - agentA.unavailableTargets.length,
      };
    })
    .sort((left, right) => left.spendDiff - right.spendDiff);

  const spendDifferences = pairedComparisons.map((row) => row.spendDiff);
  const simulationStepDifferences = pairedComparisons.map(
    (row) => row.simulationStepsDiff,
  );
  const fulfillmentDifferences = pairedComparisons.map(
    (row) => row.fulfillmentRateDiff,
  );

  return {
    armA,
    armB,
    spendVsStepsPoints: [armA, armB].flatMap((arm) =>
      arm.results.agents.map((agent) => ({
        customerId: agent.customerId,
        name: agent.name,
        layoutId: arm.id,
        layoutLabel: arm.label,
        spend: agent.spend,
        simulationSteps: agent.iterationCount,
      })),
    ),
    pairedComparisons,
    tests: {
      spend: buildPermutationResult(spendDifferences),
      simulationSteps: buildPermutationResult(simulationStepDifferences),
      fulfillment: buildPermutationResult(fulfillmentDifferences),
    },
    shopperOutcomeCounts: {
      lowerSpendInB: spendDifferences.filter((value) => value < 0).length,
      higherSpendInB: spendDifferences.filter((value) => value > 0).length,
      sameSpend: spendDifferences.filter((value) => value === 0).length,
      lowerStepsInB: simulationStepDifferences.filter((value) => value < 0).length,
      higherStepsInB: simulationStepDifferences.filter((value) => value > 0).length,
      sameSteps: simulationStepDifferences.filter((value) => value === 0).length,
    },
    narrative: {
      revenueDeltaPercent: getPercentChange(
        armA.summary.totalCheckoutRevenue,
        armB.summary.totalCheckoutRevenue,
      ),
      stepsDeltaPercent: getPercentChange(
        armA.summary.averageSimulationSteps,
        armB.summary.averageSimulationSteps,
      ),
      fulfillmentDeltaPoints:
        (armB.summary.averageFulfillmentRate -
          armA.summary.averageFulfillmentRate) *
        100,
    },
  };
}
