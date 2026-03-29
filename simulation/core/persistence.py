import json
from pathlib import Path
from plyer import filechooser
from core.config import JSON_FILE_FILTERS
from core.store import Product, Shelf


def choose_single_file(selection: list[str] | None) -> str:
    if not selection:
        return ""
    return str(selection[0])


def pick_products_file() -> str:
    selected_path = filechooser.open_file(
        path=str(Path.cwd()),
        title="Select products JSON",
        filters=JSON_FILE_FILTERS,
    )
    return choose_single_file(selected_path)


def pick_layout_load_file() -> str:
    selected_path = filechooser.open_file(
        path=str(Path.cwd()),
        title="Select layout JSON",
        filters=JSON_FILE_FILTERS,
    )
    return choose_single_file(selected_path)


def pick_layout_save_file() -> str:
    selected_path = filechooser.save_file(
        path=str(Path.cwd() / "layout.json"),
        title="Save layout JSON",
        filters=JSON_FILE_FILTERS,
    )
    return choose_single_file(selected_path)


def product_to_dict(product: Product) -> dict[str, str | float]:
    return {
        "id": product.id,
        "product_name": product.product_name,
        "product_type": product.product_type,
        "company": product.company,
        "selling_price": product.selling_price,
        "procurement_cost": product.procurement_cost,
        "discount_percent": product.discount_percent,
        "margin_percent": product.margin_percent,
    }


def parse_product(raw_product: dict, index: int) -> Product:
    return Product(
        id=str(raw_product["id"]),
        product_name=str(raw_product["product_name"]),
        product_type=str(raw_product["product_type"]),
        company=str(raw_product["company"]),
        selling_price=float(raw_product["selling_price"]),
        procurement_cost=float(raw_product["procurement_cost"]),
        discount_percent=float(raw_product["discount_percent"]),
        margin_percent=float(raw_product["margin_percent"]),
    )


def shelf_to_dict(shelf: Shelf) -> dict:
    return {
        "world_grid_position": {"x": shelf.x, "y": shelf.y},
        "type": shelf.type,
        "product_ids": [product.id for product in shelf.products],
    }


def parse_layout_data(raw_layout: dict) -> tuple[list[Shelf], list[Product], str]:
    raw_products = raw_layout.get("products")
    raw_shelves = raw_layout.get("shelves")
    if not isinstance(raw_products, list):
        raise ValueError("Layout data must contain a 'products' list.")
    if not isinstance(raw_shelves, list):
        raise ValueError("Layout data must contain a 'shelves' list.")

    currency_code = str(raw_layout.get("currency", "USD"))
    products: list[Product] = []
    for index, raw_product in enumerate(raw_products, start=1):
        if not isinstance(raw_product, dict):
            raise ValueError(f"Layout product {index} must be an object.")
        products.append(parse_product(raw_product, index))

    products_by_id = {product.id: product for product in products}
    shelves: list[Shelf] = []
    for index, raw_shelf in enumerate(raw_shelves, start=1):
        if not isinstance(raw_shelf, dict):
            raise ValueError(f"Layout shelf {index} must be an object.")

        raw_position = raw_shelf.get("world_grid_position")
        if not isinstance(raw_position, dict):
            raise ValueError(
                f"Layout shelf {index} must have a 'world_grid_position' object."
            )

        raw_product_ids = raw_shelf.get("product_ids", [])
        if not isinstance(raw_product_ids, list):
            raise ValueError(f"Layout shelf {index} must have a 'product_ids' list.")

        shelf_products: list[Product] = []
        for product_id in raw_product_ids:
            product_key = str(product_id)
            if product_key not in products_by_id:
                raise ValueError(
                    f"Layout shelf {index} references unknown product id "
                    f"'{product_key}'."
                )
            shelf_products.append(products_by_id[product_key])

        shelves.append(
            Shelf(
                int(raw_position["x"]),
                int(raw_position["y"]),
                str(raw_shelf.get("type", "shelf")),
                shelf_products,
            )
        )

    return shelves, products, currency_code


def load_products_from_json(path: str) -> tuple[list[Product], str]:
    with Path(path).open(encoding="utf-8") as file:
        raw_catalog = json.load(file)

    if not isinstance(raw_catalog, dict):
        raise ValueError("Product JSON must contain a top-level object.")

    raw_products = raw_catalog.get("products")
    if not isinstance(raw_products, list):
        raise ValueError("Product JSON must contain a 'products' list.")

    currency_code = str(raw_catalog.get("currency", "USD"))

    products: list[Product] = []
    for index, raw_product in enumerate(raw_products, start=1):
        if not isinstance(raw_product, dict):
            raise ValueError(f"Product {index} must be an object.")

        products.append(parse_product(raw_product, index))

    return products, currency_code


def save_layout_to_json(
    path: str,
    shelves: list[Shelf],
    products: list[Product],
    currency_code: str,
) -> None:
    layout_data = {
        "currency": currency_code,
        "products": [product_to_dict(product) for product in products],
        "shelves": [shelf_to_dict(shelf) for shelf in shelves],
    }
    Path(path).write_text(json.dumps(layout_data, indent=2), encoding="utf-8")


def load_layout_from_json(path: str) -> tuple[list[Shelf], list[Product], str]:
    with Path(path).open(encoding="utf-8") as file:
        raw_layout = json.load(file)

    if not isinstance(raw_layout, dict):
        raise ValueError("Layout JSON must contain a top-level object.")

    return parse_layout_data(raw_layout)
