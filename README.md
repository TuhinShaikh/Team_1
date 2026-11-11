# Lynceus data cleaning

This folder contains the cleaned case data used by the search and evaluation
teams. The goal is simple: make the case files consistent and easy to index,
without changing their meaning or silently hiding missing data.

## What I cleaned

The cleaning script:

- Reads the original `.txt` files from `Data/Original_data`.
- Removes invisible BOM characters and other control characters.
- Normalizes Unicode characters.
- Uses consistent line endings.
- Removes repeated spaces and excessive blank lines.
- Keeps the original language, punctuation, numbers, company names, and
  industry terms.
- Writes cleaned copies to `Data/Cleaned_data`.
- Calculates character counts, word counts, and a SHA-256 hash.
- Compares the files with the answer-key metadata.
- Records missing source files instead of creating fake replacements.

The original files are never overwritten.

## Current data result

The current dataset has:

- 30 source files available.
- 39 files listed in the answer-key map.
- 9 mapped files missing from the source corpus.
- 30 cleaned files generated.

The nine missing source files are recorded in `Data/manifest.csv` with the
status `missing_source`.

## Folder structure

```text
Data/
|-- Original_data/       # Original case files; do not edit
|-- Cleaned_data/        # Normalized copies for search/indexing
|-- manifest.csv         # Metadata, file paths, counts, hashes, and status
`-- quality_report.csv   # Records that need attention
scripts/
`-- data_cleaning.py     # Repeatable cleaning pipeline
```

## How to run it

Run these commands from the repository root:

```powershell
py -3 scripts\data_cleaning.py `
  --metadata ".\lynceus_answer_key_file_map.csv"
```

If the metadata CSV is still one folder above the repository, use:

```powershell
py -3 scripts\data_cleaning.py `
  --metadata "..\lynceus_answer_key_file_map.csv"
```

The command creates or updates:

```text
Data/Cleaned_data/
Data/manifest.csv
Data/quality_report.csv
```

## Example

Before cleaning, a file may contain an invisible `[BOM]` marker:

```text
[BOM]Johnson Controls   is consolidating 175 ERP systems.


The program serves employees in 150 countries.
```

After cleaning, it becomes:

```text
Johnson Controls is consolidating 175 ERP systems.

The program serves employees in 150 countries.
```

The words and meaning stay the same. Only encoding and formatting noise are
removed.

The currently missing source files are:

```text
case-472, case-291, case-251, case-281, case-985,
case-994, case-419, case-699, case-570
```

## How other teams should use the outputs

- **Search engineer:** index the files in `Data/Cleaned_data` and use
  `case_id` and `source_file` from the manifest for citations.
- **Agent engineer:** use the cleaned text and metadata fields such as
  `delivery`, `round`, and `version_given`.
- **Evaluation lead:** use the manifest as the fixed list of available and
  missing cases.
- **Evidence lead:** use the original file path, cleaned file path, and SHA-256
  hash to show where each result came from.
- **Delivery lead:** use `quality_report.csv` to track missing or questionable
  records.

## Important rule

Do not delete or edit files in `Data/Original_data`. If a source file changes,
rerun the script and commit the updated cleaned output and reports together.
