function assign(filename: string, ...productIds: string[]): Record<string, string> {
  return Object.fromEntries(productIds.map((productId) => [productId, filename]));
}

const PRODUCT_IMAGE_FILENAMES: Record<string, string> = {
  ...assign("emoji_u1f95b.png", "PRD-001", "PRD-002", "PRD-004", "PRD-028", "PRD-089"),
  ...assign("emoji_u1f963.png", "PRD-003", "PRD-049", "PRD-087", "PRD-093", "PRD-095", "PRD-103"),
  ...assign("emoji_u1f9c8.png", "PRD-005"),
  ...assign("emoji_u1f9c0.png", "PRD-006", "PRD-035", "PRD-099"),
  ...assign("emoji_u1f95a.png", "PRD-007"),
  ...assign("emoji_u1f35e.png", "PRD-008", "PRD-009", "PRD-012", "PRD-048"),
  ...assign("emoji_u1f96f.png", "PRD-010"),
  ...assign("emoji_u1fad3.png", "PRD-011", "PRD-013"),
  ...assign("emoji_u1f34c.png", "PRD-014"),
  ...assign("emoji_u1f345.png", "PRD-015", "PRD-079", "PRD-086"),
  ...assign("emoji_u1f96c.png", "PRD-016"),
  ...assign("emoji_u1f34e.png", "PRD-017"),
  ...assign("emoji_u1f951.png", "PRD-018"),
  ...assign("emoji_u1f955.png", "PRD-019"),
  ...assign("emoji_u1f966.png", "PRD-020"),
  ...assign("emoji_u1f353.png", "PRD-021", "PRD-043"),
  ...assign("emoji_u1f964.png", "PRD-022"),
  ...assign("emoji_u1f4a7.png", "PRD-023"),
  ...assign("emoji_u1f34a.png", "PRD-024"),
  ...assign("emoji_u2615.png", "PRD-025", "PRD-098"),
  ...assign("emoji_u1f379.png", "PRD-026"),
  ...assign("emoji_u1f375.png", "PRD-027"),
  ...assign("emoji_u1f37a.png", "PRD-029"),
  ...assign("emoji_u1f35f.png", "PRD-030"),
  ...assign("emoji_u1f95c.png", "PRD-031", "PRD-032", "PRD-051", "PRD-097"),
  ...assign("emoji_u1f36b.png", "PRD-033", "PRD-078"),
  ...assign("emoji_u1f968.png", "PRD-034"),
  ...assign("emoji_u1f37f.png", "PRD-036"),
  ...assign("emoji_u1f358.png", "PRD-037"),
  ...assign("emoji_u1f355.png", "PRD-038"),
  ...assign("emoji_u1f368.png", "PRD-039"),
  ...assign("emoji_u1fadb.png", "PRD-040"),
  ...assign("emoji_u1f9c7.png", "PRD-042"),
  ...assign("emoji_u1f41f.png", "PRD-044", "PRD-060", "PRD-062"),
  ...assign("emoji_u1f35a.png", "PRD-045"),
  ...assign("emoji_u1f35d.png", "PRD-046"),
  ...assign("emoji_u1fad9.png", "PRD-047", "PRD-080", "PRD-081", "PRD-082", "PRD-084"),
  ...assign("emoji_u1f36f.png", "PRD-050", "PRD-085"),
  ...assign("emoji_u1f96b.png", "PRD-052", "PRD-063", "PRD-091"),
  ...assign("emoji_u1f33d.png", "PRD-088", "PRD-092"),
  ...assign("emoji_u1f95e.png", "PRD-096"),
  ...assign("emoji_u1f357.png", "PRD-041", "PRD-054", "PRD-102"),
  ...assign("emoji_u1f969.png", "PRD-053", "PRD-057", "PRD-100", "PRD-105"),
  ...assign("emoji_u1f356.png", "PRD-055"),
  ...assign("emoji_u1f953.png", "PRD-056"),
  ...assign("emoji_u1f32d.png", "PRD-058"),
  ...assign("emoji_u1f983.png", "PRD-059"),
  ...assign("emoji_u1f364.png", "PRD-061"),
  ...assign("emoji_u1f9aa.png", "PRD-064", "PRD-065"),
  ...assign("emoji_u1f957.png", "PRD-101", "PRD-104"),
  ...assign("emoji_u1f9fc.png", "PRD-066"),
  ...assign("emoji_u1f9fb.png", "PRD-067", "PRD-072"),
  ...assign("emoji_u1f9fa.png", "PRD-068"),
  ...assign("emoji_u1f5d1.png", "PRD-069"),
  ...assign("emoji_u1f9f4.png", "PRD-070"),
  ...assign("emoji_u1f50b.png", "PRD-071"),
  ...assign("emoji_u1f950.png", "PRD-073"),
  ...assign("emoji_u1f36a.png", "PRD-074"),
  ...assign("emoji_u1f370.png", "PRD-075", "PRD-094"),
  ...assign("emoji_u1f382.png", "PRD-076"),
  ...assign("emoji_u1f9c1.png", "PRD-077"),
  ...assign("emoji_u1f336.png", "PRD-083"),
  ...assign("emoji_u1f351.png", "PRD-090"),
};

export function getProductImageFilename(productId: string): string | null {
  return PRODUCT_IMAGE_FILENAMES[productId] ?? null;
}

export function getProductImagePath(productId: string): string | null {
  const filename = getProductImageFilename(productId);
  return filename ? `/replay-assets/product-images/${filename}` : null;
}
