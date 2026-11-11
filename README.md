# Lynceus data cleaning

This folder contains the cleaned case files for our hackathon project. I kept
the cleaning deliberately simple: fix formatting issues, keep the original
meaning, and make it clear which files are missing.

## What the script does

The script:

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

The original files are kept separately and are not overwritten.

## Current results

The current dataset has:

- 30 source files available.
- 39 files listed in the answer-key map.
- 9 mapped files missing from the source corpus.
- 30 cleaned files generated.

The nine missing files are listed in `Data/manifest.csv` with the status
`missing_source`.

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

## Running the script

Run this command from the repository root:

```powershell
py -3 scripts\run_pipeline.py
```

The pipeline reads the metadata map from the repository root and runs both
cleaning and corpus generation. It creates or updates:

```text
Data/Cleaned_data/
Data/manifest.csv
Data/quality_report.csv
Data/corpus.py
```

If you need to run the two stages separately, these commands are also
available:

```powershell
py -3 scripts\build_corpus.py
```

This creates `Data/corpus.py`. It contains one record for each available
cleaned case, including the case ID, language, text, source file, delivery, and
round. Missing cases are left out of the corpus and remain visible in the
manifest.

## Small example

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
