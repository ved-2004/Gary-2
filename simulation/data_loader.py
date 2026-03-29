"""
data_loader.py

Loads customer_profiles.csv + shopping_list.csv.
Used by agents_llm.py to build LLMAgent instances.
No FastAPI dependency — works standalone inside main.py.
"""

import csv
from typing import Optional


def _parse_pipe(value: str) -> list:
    return [v.strip() for v in value.split("|") if v.strip()]


def load_customers(profiles_path: str = "../data/customer_profiles.csv", shopping_list_path: str = "../data/shopping_list.csv") -> dict:
    """
    Returns dict: customer_id -> {all profile fields + buying_list: [str]}
    """
    profiles = {}
    with open(profiles_path, newline="") as f:
        for row in csv.DictReader(f):
            profiles[row["customer_id"]] = dict(row)

    with open(shopping_list_path, newline="") as f:
        for row in csv.DictReader(f):
            cid = row["customer_id"]
            if cid not in profiles:
                continue
            list1 = _parse_pipe(row.get("shopping_list_1", ""))
            list2 = _parse_pipe(row.get("shopping_list_2", ""))
            profiles[cid]["buying_list"] = list1 + list2

    return profiles