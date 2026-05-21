from __future__ import annotations

import json
import re
import argparse
import html
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "data" / "news_corpus"
EXPORT_DIR = ROOT / "exports"
TOKEN_RE = re.compile(r"[A-Za-zÆØÅæøå]+(?:-[A-Za-zÆØÅæøå]+)*-?")
TAG_RE = re.compile(r"<[^>]+>")

MIN_TOKEN_LENGTH = 2
MAX_TOKEN_LENGTH = 32
KEEP_SINGLE_LETTERS = {"i"}
CURATED_TRANSLATIONS = {
    "af": "of; by; from",
    "alle": "all; everyone",
    "andre": "others; other",
    "arbejde": "work",
    "at": "to; that",
    "blev": "became; was",
    "blive": "become; remain",
    "bliver": "becomes; will be",
    "børn": "children",
    "dag": "day",
    "de": "they; the",
    "del": "part",
    "den": "it; that; the",
    "der": "there; who; that",
    "det": "it; that; the",
    "du": "you",
    "efter": "after",
    "eller": "or",
    "en": "a; one",
    "end": "than",
    "er": "is; are",
    "et": "a; one",
    "få": "few; get",
    "fik": "got; received",
    "flere": "more; several",
    "for": "for; to; because",
    "fra": "from",
    "får": "gets; receives",
    "før": "before",
    "første": "first",
    "går": "goes; yesterday",
    "har": "has; have",
    "havde": "had",
    "hele": "whole; entire",
    "her": "here",
    "hos": "at; with",
    "hvis": "if; whose",
    "hvor": "where",
    "i": "in",
    "ikke": "not",
    "ind": "in; into",
    "kan": "can",
    "kom": "came",
    "kommer": "comes",
    "kun": "only",
    "kunne": "could",
    "man": "one; you; people",
    "mange": "many",
    "med": "with",
    "meget": "very; much",
    "men": "but",
    "mere": "more",
    "mellem": "between",
    "mod": "against; toward",
    "må": "may; must",
    "ned": "down",
    "nu": "now",
    "nye": "new",
    "ny": "new",
    "når": "when",
    "og": "and",
    "også": "also",
    "om": "about; if; around",
    "op": "up",
    "over": "over; across",
    "på": "on; at",
    "sagde": "said",
    "sagen": "the case; the matter",
    "samtidig": "at the same time",
    "se": "see",
    "selv": "self; even",
    "seneste": "latest; most recent",
    "ser": "sees; looks",
    "sidste": "last",
    "sig": "himself; herself; itself",
    "siger": "says",
    "sin": "his; her; its own",
    "skal": "shall; must; going to",
    "skole": "school",
    "skoler": "schools",
    "skulle": "should; was supposed to",
    "som": "as; who; which",
    "stadig": "still",
    "stor": "large; big",
    "store": "large; big",
    "så": "so; then; saw",
    "til": "to; for",
    "to": "two",
    "ud": "out",
    "under": "under; during",
    "ved": "by; at; knows",
    "vil": "will; wants to",
    "viser": "shows",
    "være": "be",
    "været": "been",
}
RSS_SOURCES = [
    "https://www.prosa.dk/api/rss/news",
    "https://www.beredskabsinfo.dk/feed/",
    "https://ing.dk/rss",
    "https://www.ism.dk/handlers/DynamicRss.ashx?id=ab9a6784-6a8f-4b34-bcdf-7364bcf58d05",
    "https://uvm.dk/aktuelt/nyheder/?rss=true",
    "https://uvm.dk/umbraco/api/DynamicRss/GetRss/?pageId=31390&moduleId=8d3d6977-899a-458e-99ef-b7c091047870",
    "https://uvm.dk/umbraco/api/DynamicRss/GetRss/?pageId=31391&moduleId=34edfe6b-e837-438b-9fe9-9d53c2000e57",
    "https://uvm.dk/umbraco/api/DynamicRss/GetRss/?pageId=31392&moduleId=9c1dc3b2-e874-4d30-b6d0-9b59a4e2a2d2",
    "https://www.odense.dk/feed.aspx",
]


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


def clean_feed_text(value: str | None) -> str:
    if not value:
        return ""
    value = TAG_RE.sub(" ", value)
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


def fetch_rss_corpus(corpus_dir: Path = CORPUS_DIR) -> Path:
    corpus_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = corpus_dir / "rss_snapshot.txt"
    chunks: list[str] = []
    headers = {
        "User-Agent": "offline-flashcards educational RSS frequency builder; contact: github.com/ThinkingInSpace/offline-flashcards"
    }

    for source in RSS_SOURCES:
        request = urllib.request.Request(source, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
            root = ET.fromstring(payload)
        except Exception as error:
            print(f"Skipping feed that could not be read: {source} ({error})")
            continue

        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        for item in items:
            title = item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title")
            description = (
                item.findtext("description")
                or item.findtext("{http://www.w3.org/2005/Atom}summary")
                or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded")
            )
            chunks.append(clean_feed_text(title))
            chunks.append(clean_feed_text(description))

    snapshot_path.write_text("\n".join(chunk for chunk in chunks if chunk), encoding="utf-8")
    return snapshot_path


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
            "English": CURATED_TRANSLATIONS.get(word, ""),
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
    parser = argparse.ArgumentParser(description="Build a Danish news top-500 deck.")
    parser.add_argument(
        "--fetch-rss",
        action="store_true",
        help="Fetch configured RSS title/description text into data/news_corpus/rss_snapshot.txt before building.",
    )
    args = parser.parse_args()

    if args.fetch_rss:
        snapshot_path = fetch_rss_corpus()
        print(f"Fetched RSS corpus into {snapshot_path}")

    deck = build_news_top_500()
    export_news_top_500(deck)
    print(f"Exported {len(deck)} news-frequency words from {CORPUS_DIR}")


if __name__ == "__main__":
    main()
