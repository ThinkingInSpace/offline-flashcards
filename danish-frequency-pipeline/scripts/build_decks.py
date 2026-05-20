from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd


POS_MAP = {
    "A": "adjective",
    "C": "conjunction",
    "D": "adverb",
    "NC": "noun",
    "P": "pronoun",
    "T": "preposition",
    "U": "function_word",
    "V": "verb",
}

ALLOWED_POS = set(POS_MAP)
CRITICAL_KEEP = {"at", "som", "der", "og", "på", "til", "jo", "vel", "dog"}
MALFORMED_PATTERN = re.compile(r"[@0-9_]|[^\wæøåÆØÅ-]", re.UNICODE)


def cefr_for_rank(rank: int) -> str:
    if rank <= 500:
        return "A1"
    if rank <= 1000:
        return "A2"
    return "B1/B2"


def tags_for(pos: str, rank: int) -> list[str]:
    tags = ["core", pos]
    if rank <= 500:
        tags.append("core_500")
    if rank <= 1000:
        tags.append("core_1000")
    tags.append("core_2000")
    return tags


def is_useful_learning_token(pos_code: str, lemma: str) -> bool:
    lemma = lemma.strip()
    if lemma in CRITICAL_KEEP:
        return True
    if pos_code not in ALLOWED_POS:
        return False
    if not lemma or len(lemma) > 40:
        return False
    if MALFORMED_PATTERN.search(lemma):
        return False
    return True


def parse_frequency_file(source_path: Path) -> pd.DataFrame:
    rows: list[dict] = []
    with source_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            parts = raw_line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue

            pos_code, lemma, frequency = parts
            if not is_useful_learning_token(pos_code, lemma):
                continue

            rows.append({
                "lemma": lemma,
                "english": None,
                "pos": POS_MAP.get(pos_code, "function_word"),
                "pos_code": pos_code,
                "normalized_frequency": float(frequency),
            })

    records = []
    for rank, row in enumerate(rows[:2000], start=1):
        pos = row["pos"]
        records.append({
            "lemma": row["lemma"],
            "english": [],
            "pos": pos,
            "frequency_rank": rank,
            "normalized_frequency": row["normalized_frequency"],
            "cefr_estimate": cefr_for_rank(rank),
            "tags": tags_for(pos, rank),
            "example_da": "",
            "example_en": "",
        })

    return pd.DataFrame.from_records(records)


def staged_decks(core: pd.DataFrame) -> Iterable[tuple[str, pd.DataFrame]]:
    yield "core_500", core.head(500).copy()
    yield "core_1000", core.head(1000).copy()
    yield "core_2000", core.head(2000).copy()
