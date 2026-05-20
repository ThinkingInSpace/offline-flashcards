from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


BOM_UTF8 = "utf-8-sig"


def record_for_json(row: pd.Series) -> dict:
    return {
        "lemma": row["lemma"],
        "english": row["english"],
        "pos": row["pos"],
        "frequency_rank": int(row["frequency_rank"]),
        "normalized_frequency": float(row["normalized_frequency"]),
        "example_da": row.get("example_da", ""),
        "example_en": row.get("example_en", ""),
        "cefr_estimate": row["cefr_estimate"],
        "tags": row["tags"],
    }


def export_json(deck_name: str, deck: pd.DataFrame, export_dir: Path) -> None:
    records = [record_for_json(row) for _, row in deck.iterrows()]
    path = export_dir / f"{deck_name}.json"
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding=BOM_UTF8,
    )


def export_csv(deck_name: str, deck: pd.DataFrame, export_dir: Path) -> None:
    output = deck.copy()
    output["tags"] = output["tags"].apply(lambda values: " ".join(values))
    output["english"] = output["english"].apply(lambda values: "; ".join(values) if isinstance(values, list) else values)
    output.to_csv(export_dir / f"{deck_name}.csv", index=False, encoding=BOM_UTF8)


def export_tsv(deck_name: str, deck: pd.DataFrame, export_dir: Path) -> None:
    output = deck[["lemma", "english", "pos", "frequency_rank", "tags"]].copy()
    output["english"] = output["english"].apply(lambda values: "; ".join(values) if isinstance(values, list) else (values or ""))
    output["tags"] = output["tags"].apply(lambda values: " ".join(values))
    output.to_csv(
        export_dir / f"anki_{deck_name}.tsv",
        sep="\t",
        index=False,
        header=False,
        encoding=BOM_UTF8,
    )


def export_all(deck_name: str, deck: pd.DataFrame, export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    export_json(deck_name, deck, export_dir)
    export_csv(deck_name, deck, export_dir)
    export_tsv(deck_name, deck, export_dir)
