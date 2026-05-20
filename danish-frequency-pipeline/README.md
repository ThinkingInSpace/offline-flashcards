# Danish Frequency Learning Pipeline

Lightweight pipeline for building staged Danish reading-comprehension decks from DSL lemma frequency data.

The source frequency list comes from Det Danske Sprog- og Litteraturselskab (DSL):

- Primary resource: https://korpus.dsl.dk/resources/details/freq-lemmas.html
- Dataset metadata: https://sprogteknologi.dk/dataset/10-000-mest-frekvente-lemmaer

The DSL resource is a ZIP file containing a plain-text tab-separated lemma list. Each source row has:

```text
POS<TAB>lemma<TAB>normalized_frequency
```

## What This Builds

The pipeline creates the top 2000 useful Danish lemmas for learning-oriented reading comprehension.

It exports staged decks:

- `core_500`
- `core_1000`
- `core_2000`

Each record has this shape:

```json
{
  "lemma": "være",
  "english": null,
  "pos": "verb",
  "frequency_rank": 2,
  "normalized_frequency": 0.0309,
  "cefr_estimate": "A1",
  "tags": ["core", "verb", "core_500", "core_1000", "core_2000"]
}
```

## How To Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
./run.sh
```

On Windows PowerShell:

```powershell
python scripts/run_pipeline.py
```

## Outputs

Generated files are written to `exports/`:

- `core_500.json`
- `core_1000.json`
- `core_2000.json`
- `core_500.csv`
- `core_1000.csv`
- `core_2000.csv`
- `anki_core_500.tsv`
- `anki_core_1000.tsv`
- `anki_core_2000.tsv`

All exports use UTF-8 with BOM (`utf-8-sig`) for better Excel and Anki compatibility.

## Importing Into Anki

Use the `anki_*.tsv` files.

TSV columns:

```text
lemma<TAB>english<TAB>pos<TAB>frequency_rank<TAB>tags
```

The `english` field is intentionally blank. The frequency list is a Danish source list, not a translation dictionary. Add translations manually or through a separate reviewed translation workflow.

In Anki:

1. Choose `File > Import`.
2. Select one of the `anki_*.tsv` files.
3. Use tab as the field separator.
4. Map fields to your note type.
5. Use the final column as tags if your Anki import settings support it.

## POS Meanings

The pipeline maps DSL POS tags as follows:

| DSL tag | Meaning |
| --- | --- |
| A | adjective |
| C | conjunction |
| D | adverb |
| NC | noun |
| P | pronoun |
| T | preposition |
| U | function_word |
| V | verb |

Proper nouns, numerals, part-word artifacts, punctuation fragments, and malformed tokens are filtered out.

Critical Danish comprehension words are explicitly kept, including:

```text
at, som, der, og, på, til, jo, vel, dog
```

## CEFR Estimate

This is a rough frequency-based staging estimate:

- ranks 1-500: `A1`
- ranks 501-1000: `A2`
- ranks 1001-2000: `B1/B2`

## Deck Philosophy

These decks are for reading comprehension, not complete language mastery. They prioritize common lemmas, function words, discourse markers, prepositions, pronouns, modal verbs, and high-utility content words.

The pipeline deliberately stays simple:

- deterministic
- minimal dependencies
- source-preserving
- easy to rerun
- translation-neutral

## License And Credit

This project uses DSL open language resources. Review DSL's terms before redistribution or public use:

https://korpus.dsl.dk/resources/licences/dsl-open.html
