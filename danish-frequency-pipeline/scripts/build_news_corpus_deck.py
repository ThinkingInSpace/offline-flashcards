from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "data" / "news_corpus"
EXPORT_DIR = ROOT / "exports"
TOKEN_RE = re.compile(r"[A-Za-zÆØÅæøå]+(?:-[A-Za-zÆØÅæøå]+)?")

MIN_TOKEN_LENGTH = 2
MAX_TOKEN_LENGTH = 32
KEEP_SINGLE_LETTERS = {"i"}


def valid_token(token: str) -> bool:
    if token in KEEP_SINGLE_LETTERS:
        return True
    if len(token) < MIN_TOKEN_LENGTH or len(token) > MAX_TOKEN_LENGTH:
        return False
    if token.startswith("-") or token.endswith("-"):
        return False
    return True


def iter_corpus_texts(corpus_dir: Path) -> list[str]:
    paths = sorted(corpus_dir.glob("*.txt")) + sorted(corpus_dir.glob("*.md"))
    texts = []
    for path in paths:
        texts.append(path.read_text(encoding="utf-8-sig", errors="replace"))
    return texts


def build_news_top_500(corpus_dir: Path = CORPUS_DIR) -> pd.DataFrame:
    counter: Counter[str] = Counter()
    for text in iter_corpus_texts(corpus_dir):
        for raw_token in TOKEN_RE.findall(text):
            token = raw_token.lower()
            if valid_token(token):
                counter[token] += 1

    if not counter:
        raise RuntimeError(
            f"No corpus tokens found. Add .txt files to {corpus_dir} before running."
        )

    total = sum(counter.values())
    records = []
    for rank, (word, count) in enumerate(counter.most_common(500), start=1):
        records.append({
            "Danish": word,
            "English": "",
            "PartOfSpeech": "",
            "Example": "",
            "Tags": "danish::news_top_500",
            "frequency_rank": rank,
            "count": count,
            "normalized_frequency": count / total,
        })

    return pd.DataFrame.from_records(records)


def export_news_top_500(deck: pd.DataFrame, export_dir: Path = EXPORT_DIR) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    deck.to_csv(export_dir / "news_top_500.csv", index=False, encoding="utf-8-sig")
    deck.to_json(
        export_dir / "news_top_500.json",
        orient="records",
        force_ascii=False,
        indent=2,
    )

    anki = deck[["Danish", "English", "PartOfSpeech", "frequency_rank", "Tags"]].copy()
    anki.to_csv(
        export_dir / "anki_news_top_500.tsv",
        sep="\t",
        index=False,
        header=False,
        encoding="utf-8-sig",
    )


def main() -> None:
    deck = build_news_top_500()
    export_news_top_500(deck)
    print(f"Exported {len(deck)} news-frequency words from {CORPUS_DIR}")


if __name__ == "__main__":
    main()
