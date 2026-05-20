from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


POS_CANDIDATES = {
    "adjective": ["adj"],
    "adverb": ["adv"],
    "conjunction": ["conj"],
    "noun": ["noun"],
    "pronoun": ["pron", "det", "article"],
    "preposition": ["prep"],
    "function_word": ["particle", "conj", "adv", "prep", "article"],
    "verb": ["verb"],
}

BORING_GLOSSES = {
    "plural",
    "singular",
    "definite",
    "indefinite",
}


def clean_translation(text: str, lemma: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\([^)]*\)", "", text).strip()
    text = text.split(";")[0].strip()
    text = text.split(":")[0].strip()
    text = text.strip(" .,!?:;")
    if text.lower() == lemma.lower():
        return ""
    if len(text) > 42 or not text:
        return ""
    if text.lower() in BORING_GLOSSES:
        return ""
    return text


def candidates_from_sense(sense: dict[str, Any], lemma: str) -> list[str]:
    candidates: list[str] = []

    for link in sense.get("links", []):
        if isinstance(link, list) and link:
            cleaned = clean_translation(str(link[0]), lemma)
            if cleaned:
                candidates.append(cleaned)

    for gloss in sense.get("glosses", []):
        cleaned = clean_translation(str(gloss), lemma)
        if cleaned:
            candidates.append(cleaned)

    return candidates


def first_example(entry: dict[str, Any]) -> tuple[str, str]:
    for sense in entry.get("senses", []):
        for example in sense.get("examples", []) or []:
            da = example.get("text", "")
            en = example.get("english") or example.get("translation") or ""
            if da and en:
                return da, en
    return "", ""


def build_translation_index(kaikki_path: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    with kaikki_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            entry = json.loads(line)
            if entry.get("lang_code") != "da":
                continue
            word = entry.get("word")
            pos = entry.get("pos")
            if word and pos:
                index[(word, pos)].append(entry)
    return index


def lookup_entries(
    index: dict[tuple[str, str], list[dict[str, Any]]],
    lemma: str,
    pos: str,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for kaikki_pos in POS_CANDIDATES.get(pos, []):
        entries.extend(index.get((lemma, kaikki_pos), []))
    return entries


def enrich_core(core: pd.DataFrame, kaikki_path: Path) -> pd.DataFrame:
    index = build_translation_index(kaikki_path)
    enriched_rows: list[dict[str, Any]] = []

    for row in core.to_dict("records"):
        entries = lookup_entries(index, row["lemma"], row["pos"])
        translations: list[str] = []
        example_da = ""
        example_en = ""

        for entry in entries:
            if not example_da:
                example_da, example_en = first_example(entry)
            for sense in entry.get("senses", []):
                for candidate in candidates_from_sense(sense, row["lemma"]):
                    if candidate not in translations:
                        translations.append(candidate)
                if len(translations) >= 3:
                    break
            if len(translations) >= 3:
                break

        row["english"] = translations[:3]
        row["example_da"] = example_da
        row["example_en"] = example_en
        enriched_rows.append(row)

    return pd.DataFrame.from_records(enriched_rows)
