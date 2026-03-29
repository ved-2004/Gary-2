import pyray as pr

from core.config import PRODUCT_IMAGES_DIR


def _assign(filename: str, *product_ids: str) -> dict[str, str]:
    return {product_id: filename for product_id in product_ids}


PRODUCT_IMAGE_FILENAMES: dict[str, str] = {
    # Dairy
    **_assign("emoji_u1f95b.png", "PRD-001", "PRD-002", "PRD-004", "PRD-028", "PRD-089"),
    **_assign("emoji_u1f963.png", "PRD-003", "PRD-049", "PRD-087", "PRD-093", "PRD-095", "PRD-103"),
    **_assign("emoji_u1f9c8.png", "PRD-005"),
    **_assign("emoji_u1f9c0.png", "PRD-006", "PRD-035", "PRD-099"),
    **_assign("emoji_u1f95a.png", "PRD-007"),
    # Bread / bakery basics
    **_assign("emoji_u1f35e.png", "PRD-008", "PRD-009", "PRD-012", "PRD-048"),
    **_assign("emoji_u1f96f.png", "PRD-010"),
    **_assign("emoji_u1fad3.png", "PRD-011", "PRD-013"),
    # Produce
    **_assign("emoji_u1f34c.png", "PRD-014"),
    **_assign("emoji_u1f345.png", "PRD-015", "PRD-079", "PRD-086"),
    **_assign("emoji_u1f96c.png", "PRD-016"),
    **_assign("emoji_u1f34e.png", "PRD-017"),
    **_assign("emoji_u1f951.png", "PRD-018"),
    **_assign("emoji_u1f955.png", "PRD-019"),
    **_assign("emoji_u1f966.png", "PRD-020"),
    **_assign("emoji_u1f353.png", "PRD-021", "PRD-043"),
    # Beverages
    **_assign("emoji_u1f964.png", "PRD-022"),
    **_assign("emoji_u1f4a7.png", "PRD-023"),
    **_assign("emoji_u1f34a.png", "PRD-024"),
    **_assign("emoji_u2615.png", "PRD-025", "PRD-098"),
    **_assign("emoji_u1f379.png", "PRD-026"),
    **_assign("emoji_u1f375.png", "PRD-027"),
    **_assign("emoji_u1f37a.png", "PRD-029"),
    # Snacks / frozen / pantry
    **_assign("emoji_u1f35f.png", "PRD-030"),
    **_assign("emoji_u1f95c.png", "PRD-031", "PRD-032", "PRD-051", "PRD-097"),
    **_assign("emoji_u1f36b.png", "PRD-033", "PRD-078"),
    **_assign("emoji_u1f968.png", "PRD-034"),
    **_assign("emoji_u1f37f.png", "PRD-036"),
    **_assign("emoji_u1f358.png", "PRD-037"),
    **_assign("emoji_u1f355.png", "PRD-038"),
    **_assign("emoji_u1f368.png", "PRD-039"),
    **_assign("emoji_u1fadb.png", "PRD-040"),
    **_assign("emoji_u1f9c7.png", "PRD-042"),
    **_assign("emoji_u1f41f.png", "PRD-044", "PRD-060", "PRD-062"),
    **_assign("emoji_u1f35a.png", "PRD-045"),
    **_assign("emoji_u1f35d.png", "PRD-046"),
    **_assign("emoji_u1fad9.png", "PRD-047", "PRD-080", "PRD-081", "PRD-082", "PRD-084"),
    **_assign("emoji_u1f36f.png", "PRD-050", "PRD-085"),
    **_assign("emoji_u1f96b.png", "PRD-052", "PRD-063", "PRD-091"),
    **_assign("emoji_u1f33d.png", "PRD-088", "PRD-092"),
    **_assign("emoji_u1f95e.png", "PRD-096"),
    # Meat / seafood / deli
    **_assign("emoji_u1f357.png", "PRD-041", "PRD-054", "PRD-102"),
    **_assign("emoji_u1f969.png", "PRD-053", "PRD-057", "PRD-100", "PRD-105"),
    **_assign("emoji_u1f356.png", "PRD-055"),
    **_assign("emoji_u1f953.png", "PRD-056"),
    **_assign("emoji_u1f32d.png", "PRD-058"),
    **_assign("emoji_u1f983.png", "PRD-059"),
    **_assign("emoji_u1f364.png", "PRD-061"),
    **_assign("emoji_u1f9aa.png", "PRD-064", "PRD-065"),
    **_assign("emoji_u1f957.png", "PRD-101", "PRD-104"),
    # Household
    **_assign("emoji_u1f9fc.png", "PRD-066"),
    **_assign("emoji_u1f9fb.png", "PRD-067", "PRD-072"),
    **_assign("emoji_u1f9fa.png", "PRD-068"),
    **_assign("emoji_u1f5d1.png", "PRD-069"),
    **_assign("emoji_u1f9f4.png", "PRD-070"),
    **_assign("emoji_u1f50b.png", "PRD-071"),
    # Bakery / breakfast
    **_assign("emoji_u1f950.png", "PRD-073"),
    **_assign("emoji_u1f36a.png", "PRD-074"),
    **_assign("emoji_u1f370.png", "PRD-075", "PRD-094"),
    **_assign("emoji_u1f382.png", "PRD-076"),
    **_assign("emoji_u1f9c1.png", "PRD-077"),
    # Condiments / canned / extras
    **_assign("emoji_u1f336.png", "PRD-083"),
    **_assign("emoji_u1f351.png", "PRD-090"),
}


def get_product_image_filename(product_id: str) -> str | None:
    return PRODUCT_IMAGE_FILENAMES.get(product_id)


def load_product_textures() -> dict[str, object]:
    textures: dict[str, object] = {}
    if not PRODUCT_IMAGES_DIR.exists():
        return textures

    for filename in sorted(set(PRODUCT_IMAGE_FILENAMES.values())):
        image_path = PRODUCT_IMAGES_DIR / filename
        if image_path.exists():
            textures[filename] = pr.load_texture(str(image_path))
    return textures


def unload_product_textures(product_textures: dict[str, object]) -> None:
    for texture in product_textures.values():
        pr.unload_texture(texture)
