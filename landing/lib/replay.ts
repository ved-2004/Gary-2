export interface ReplayMetadata {
  timestamp: string;
  model: string;
  reasoningEffort: string | null;
  agentCount: number;
  maxIterationsPerAgent: number;
  seed: number | null;
}

export interface ReplayProduct {
  id: string;
  productName: string;
  productType: string;
  company: string;
  sellingPrice: number;
  procurementCost: number;
  discountPercent: number;
  marginPercent: number;
}

export interface ReplayShelf {
  x: number;
  y: number;
  type: string;
  productIds: string[];
}

export interface ReplayCartItem {
  productId: string;
  productName: string;
  company: string;
  sellingPrice: number;
}

export interface ReplayStep {
  iteration: number;
  rawAction: string;
  rawProductId: string | null;
  rawReasoning: string;
  action: string;
  productId: string | null;
  success: boolean;
  positionBeforeX: number;
  positionBeforeY: number;
  positionX: number;
  positionY: number;
  inventory: ReplayCartItem[];
  checkedOutItems: ReplayCartItem[];
}

export interface ReplayAgent {
  customerId: string;
  name: string;
  spriteName: string;
  spawnX: number;
  spawnY: number;
  shoppingTargets: string[];
  unavailableTargets: string[];
  maxIterations: number;
  completionReason: string;
  steps: ReplayStep[];
}

export interface ReplayLayout {
  currency: string;
  products: ReplayProduct[];
  shelves: ReplayShelf[];
}

export interface ReplayTrajectory {
  metadata: ReplayMetadata;
  layout: ReplayLayout;
  agents: ReplayAgent[];
  maxSteps: number;
}

export interface ReplayBounds {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
  width: number;
  height: number;
}

export interface ReplayAgentSnapshot {
  x: number;
  y: number;
  isFinished: boolean;
  isWaiting: boolean;
  visibleStepCount: number;
  step: ReplayStep | null;
}

const DEFAULT_BOUNDS: ReplayBounds = {
  minX: -1,
  maxX: 1,
  minY: -1,
  maxY: 1,
  width: 3,
  height: 3,
};

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

function optionalString(value: unknown, label: string): string | null {
  if (value == null) {
    return null;
  }
  return expectString(value, label);
}

function optionalNumber(value: unknown, label: string): number | null {
  if (value == null) {
    return null;
  }
  return expectNumber(value, label);
}

function parseCartItem(rawItem: unknown, label: string): ReplayCartItem {
  const item = expectRecord(rawItem, label);

  return {
    productId:
      typeof item.id === "string"
        ? item.id
        : typeof item.product_id === "string"
          ? item.product_id
          : "",
    productName: expectString(item.product_name, `${label}.product_name`),
    company:
      typeof item.company === "string"
        ? item.company
        : "Unknown company",
    sellingPrice:
      typeof item.selling_price === "number"
        ? item.selling_price
        : 0,
  };
}

function parseProduct(rawProduct: unknown, label: string): ReplayProduct {
  const product = expectRecord(rawProduct, label);

  return {
    id: expectString(product.id, `${label}.id`),
    productName: expectString(product.product_name, `${label}.product_name`),
    productType: expectString(product.product_type, `${label}.product_type`),
    company: expectString(product.company, `${label}.company`),
    sellingPrice: expectNumber(product.selling_price, `${label}.selling_price`),
    procurementCost: expectNumber(
      product.procurement_cost,
      `${label}.procurement_cost`,
    ),
    discountPercent: expectNumber(
      product.discount_percent,
      `${label}.discount_percent`,
    ),
    marginPercent: expectNumber(product.margin_percent, `${label}.margin_percent`),
  };
}

function parseShelf(rawShelf: unknown, label: string): ReplayShelf {
  const shelf = expectRecord(rawShelf, label);
  const position = expectRecord(
    shelf.world_grid_position,
    `${label}.world_grid_position`,
  );

  return {
    x: expectNumber(position.x, `${label}.world_grid_position.x`),
    y: expectNumber(position.y, `${label}.world_grid_position.y`),
    type: expectString(shelf.type, `${label}.type`),
    productIds:
      shelf.product_ids == null
        ? []
        : expectStringArray(shelf.product_ids, `${label}.product_ids`),
  };
}

function parseStep(rawStep: unknown, label: string): ReplayStep {
  const step = expectRecord(rawStep, label);
  const positionBefore = expectRecord(
    step.position_before,
    `${label}.position_before`,
  );
  const positionAfter = expectRecord(step.position_after, `${label}.position_after`);

  return {
    iteration: expectNumber(step.iteration, `${label}.iteration`),
    rawAction: expectString(step.raw_action, `${label}.raw_action`),
    rawProductId: optionalString(
      step.raw_product_id,
      `${label}.raw_product_id`,
    ),
    rawReasoning: expectString(step.raw_reasoning, `${label}.raw_reasoning`),
    action: expectString(step.adjusted_action, `${label}.adjusted_action`),
    productId: optionalString(
      step.adjusted_product_id,
      `${label}.adjusted_product_id`,
    ),
    success:
      typeof step.success === "boolean"
        ? step.success
        : false,
    positionBeforeX: expectNumber(
      positionBefore.x,
      `${label}.position_before.x`,
    ),
    positionBeforeY: expectNumber(
      positionBefore.y,
      `${label}.position_before.y`,
    ),
    positionX: expectNumber(positionAfter.x, `${label}.position_after.x`),
    positionY: expectNumber(positionAfter.y, `${label}.position_after.y`),
    inventory: expectArray(step.inventory_after ?? [], `${label}.inventory_after`).map(
      (item, index) => parseCartItem(item, `${label}.inventory_after[${index}]`),
    ),
    checkedOutItems: expectArray(
      step.checked_out_items_after ?? [],
      `${label}.checked_out_items_after`,
    ).map((item, index) =>
      parseCartItem(item, `${label}.checked_out_items_after[${index}]`),
    ),
  };
}

function parseAgent(rawAgent: unknown, label: string): ReplayAgent {
  const agent = expectRecord(rawAgent, label);
  const spawnPosition = expectRecord(
    agent.spawn_position,
    `${label}.spawn_position`,
  );

  return {
    customerId: expectString(agent.customer_id, `${label}.customer_id`),
    name: expectString(agent.name, `${label}.name`),
    spriteName: expectString(agent.sprite_name, `${label}.sprite_name`),
    spawnX: expectNumber(spawnPosition.x, `${label}.spawn_position.x`),
    spawnY: expectNumber(spawnPosition.y, `${label}.spawn_position.y`),
    shoppingTargets:
      agent.shopping_targets == null
        ? []
        : expectStringArray(agent.shopping_targets, `${label}.shopping_targets`),
    unavailableTargets:
      agent.unavailable_targets == null
        ? []
        : expectStringArray(
            agent.unavailable_targets,
            `${label}.unavailable_targets`,
          ),
    maxIterations:
      typeof agent.max_iterations === "number"
        ? agent.max_iterations
        : 0,
    completionReason:
      typeof agent.completion_reason === "string"
        ? agent.completion_reason
        : "",
    steps: expectArray(agent.steps ?? [], `${label}.steps`).map((step, index) =>
      parseStep(step, `${label}.steps[${index}]`),
    ),
  };
}

export function parseReplayTrajectory(rawValue: unknown): ReplayTrajectory {
  const raw = expectRecord(rawValue, "Replay trajectory");
  const metadata = expectRecord(raw.metadata, "Replay trajectory.metadata");
  const layout = expectRecord(raw.layout, "Replay trajectory.layout");
  const agents = expectArray(raw.agents ?? [], "Replay trajectory.agents").map(
    (agent, index) => parseAgent(agent, `Replay trajectory.agents[${index}]`),
  );

  return {
    metadata: {
      timestamp: expectString(metadata.timestamp, "Replay metadata.timestamp"),
      model: expectString(metadata.model, "Replay metadata.model"),
      reasoningEffort: optionalString(
        metadata.reasoning_effort,
        "Replay metadata.reasoning_effort",
      ),
      agentCount: expectNumber(metadata.agent_count, "Replay metadata.agent_count"),
      maxIterationsPerAgent: expectNumber(
        metadata.max_iterations_per_agent,
        "Replay metadata.max_iterations_per_agent",
      ),
      seed: optionalNumber(metadata.seed, "Replay metadata.seed"),
    },
    layout: {
      currency:
        typeof layout.currency === "string"
          ? layout.currency
          : "USD",
      products: expectArray(layout.products ?? [], "Replay layout.products").map(
        (product, index) =>
          parseProduct(product, `Replay layout.products[${index}]`),
      ),
      shelves: expectArray(layout.shelves ?? [], "Replay layout.shelves").map(
        (shelf, index) => parseShelf(shelf, `Replay layout.shelves[${index}]`),
      ),
    },
    agents,
    maxSteps: agents.reduce(
      (maxSteps, agent) => Math.max(maxSteps, agent.steps.length),
      0,
    ),
  };
}

export function getReplayBounds(
  trajectory: ReplayTrajectory,
  padding = 1,
): ReplayBounds {
  const allX: number[] = [];
  const allY: number[] = [];

  for (const shelf of trajectory.layout.shelves) {
    allX.push(shelf.x);
    allY.push(shelf.y);
  }

  for (const agent of trajectory.agents) {
    allX.push(agent.spawnX);
    allY.push(agent.spawnY);
    for (const step of agent.steps) {
      allX.push(step.positionX);
      allY.push(step.positionY);
    }
  }

  if (allX.length === 0 || allY.length === 0) {
    return DEFAULT_BOUNDS;
  }

  const minX = Math.min(...allX) - padding;
  const maxX = Math.max(...allX) + padding;
  const minY = Math.min(...allY) - padding;
  const maxY = Math.max(...allY) + padding;

  return {
    minX,
    maxX,
    minY,
    maxY,
    width: maxX - minX + 1,
    height: maxY - minY + 1,
  };
}

export function getReplayAgentSnapshot(
  agent: ReplayAgent,
  currentStep: number,
): ReplayAgentSnapshot {
  if (currentStep < 0 || agent.steps.length === 0) {
    return {
      x: agent.spawnX,
      y: agent.spawnY,
      isFinished: false,
      isWaiting: true,
      visibleStepCount: 0,
      step: null,
    };
  }

  if (currentStep < agent.steps.length) {
    return {
      x: agent.steps[currentStep].positionX,
      y: agent.steps[currentStep].positionY,
      isFinished: false,
      isWaiting: false,
      visibleStepCount: currentStep + 1,
      step: agent.steps[currentStep],
    };
  }

  const lastStep = agent.steps[agent.steps.length - 1];
  return {
    x: lastStep.positionX,
    y: lastStep.positionY,
    isFinished: true,
    isWaiting: false,
    visibleStepCount: agent.steps.length,
    step: lastStep,
  };
}

export function formatCompletionReason(reason: string): string {
  if (!reason) {
    return "Replay ended";
  }

  return reason
    .split("_")
    .filter(Boolean)
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(" ");
}

export function formatCurrency(amount: number, currencyCode: string): string {
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currencyCode,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currencyCode} ${amount.toFixed(2)}`;
  }
}

export function getReplayStepLabel(currentStep: number, maxSteps: number): string {
  const displayStep = Math.max(0, currentStep + 1);
  return `Step ${displayStep} / ${maxSteps}`;
}

export function getAgentSpritePath(spriteName: string): string {
  return `/replay-assets/PeopleSprites/${spriteName}`;
}
