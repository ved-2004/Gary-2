import csv
from pathlib import Path
from agents import CustomerNeed, CustomerProfile
from core.config import CUSTOMER_PROFILES_PATH, SHOPPING_LIST_PATH


def split_pipe_values(raw_value: str) -> tuple[str, ...]:
    return tuple(
        value.strip()
        for value in raw_value.split("|")
        if value.strip()
    )


def parse_csv_bool(raw_value: str) -> bool:
    return raw_value.strip().lower() in {"1", "true", "yes", "y"}


def load_customer_profiles(
    customer_profiles_path: Path = CUSTOMER_PROFILES_PATH,
    shopping_list_path: Path = SHOPPING_LIST_PATH,
) -> list[CustomerProfile]:
    with customer_profiles_path.open(newline="", encoding="utf-8") as customer_file:
        customer_rows = list(csv.DictReader(customer_file))
    with shopping_list_path.open(newline="", encoding="utf-8") as shopping_file:
        shopping_rows = list(csv.DictReader(shopping_file))

    shopping_by_customer: dict[str, tuple[str, tuple[CustomerNeed, ...]]] = {}
    for row in shopping_rows:
        customer_id = row["customer_id"].strip()
        shopping_needs: list[CustomerNeed] = []
        need_index = 1
        while f"need_{need_index}" in row:
            need_name = row.get(f"need_{need_index}", "").strip()
            need_type = row.get(f"need_{need_index}_product_type", "").strip()
            shopping_list = split_pipe_values(row.get(f"shopping_list_{need_index}", ""))
            if need_name:
                shopping_needs.append(
                    CustomerNeed(
                        name=need_name,
                        product_type=need_type,
                        shopping_list=shopping_list,
                    )
                )
            need_index += 1

        shopping_by_customer[customer_id] = (
            row.get("name", "").strip(),
            tuple(shopping_needs),
        )

    profiles: list[CustomerProfile] = []
    seen_customer_ids: set[str] = set()
    for row in customer_rows:
        customer_id = row["customer_id"].strip()
        customer_name = row["name"].strip()
        if customer_id not in shopping_by_customer:
            raise ValueError(
                f"Customer {customer_id} is missing from {shopping_list_path.name}."
            )

        shopping_name, shopping_needs = shopping_by_customer[customer_id]
        if shopping_name and shopping_name != customer_name:
            raise ValueError(
                f"Customer name mismatch for {customer_id}: "
                f"{customer_name!r} vs {shopping_name!r}."
            )

        profiles.append(
            CustomerProfile(
                customer_id=customer_id,
                name=customer_name,
                age=int(row["age"]),
                gender=row["gender"].strip(),
                income_bracket=row["income_bracket"].strip(),
                churned=parse_csv_bool(row["churned"]),
                marital_status=row["marital_status"].strip(),
                number_of_children=int(row["number_of_children"]),
                education_level=row["education_level"].strip(),
                occupation=row["occupation"].strip(),
                race=row["race"].strip(),
                disability=parse_csv_bool(row["disability"]),
                height_cm=int(row["height"]),
                customer_needs=split_pipe_values(row["customer_needs"]),
                purchased_alcohol_before=parse_csv_bool(
                    row["purchased_alcohol_before"]
                ),
                fitness_level=row["fitness_level"].strip(),
                organic_preference=parse_csv_bool(row["organic_preference"]),
                total_historical_purchase=float(row["total_historical_purchase"]),
                avg_purchase_value=float(row["avg_purchase_value"]),
                shopping_needs=shopping_needs,
            )
        )
        seen_customer_ids.add(customer_id)

    extra_customer_ids = sorted(set(shopping_by_customer) - seen_customer_ids)
    if extra_customer_ids:
        raise ValueError(
            "Shopping list rows are missing customer profile rows for: "
            + ", ".join(extra_customer_ids)
        )

    profiles.sort(key=lambda profile: profile.customer_id)
    return profiles
