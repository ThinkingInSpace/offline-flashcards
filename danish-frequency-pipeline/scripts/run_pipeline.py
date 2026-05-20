from __future__ import annotations

from pathlib import Path

from build_decks import parse_frequency_file, staged_decks
from download_source import download_and_extract, download_kaikki
from enrich_translations import enrich_core
from export_decks import export_all


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EXPORT_DIR = ROOT / "exports"


def main() -> None:
    source_path = download_and_extract(DATA_DIR)
    kaikki_path = download_kaikki(DATA_DIR)
    core = parse_frequency_file(source_path)
    if len(core) < 2000:
        raise RuntimeError(f"Expected 2000 useful lemmas, found {len(core)}.")
    core = enrich_core(core, kaikki_path)

    for deck_name, deck in staged_decks(core):
        export_all(deck_name, deck, EXPORT_DIR)

    print(f"Source: {source_path}")
    print(f"Translations: {kaikki_path}")
    print(f"Exported {len(core)} records into {EXPORT_DIR}")


if __name__ == "__main__":
    main()
