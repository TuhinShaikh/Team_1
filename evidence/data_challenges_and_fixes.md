# Data engineering: challenges and fixes

Owner: Tuhin (Data Engineer). Recorded by Ahmad (Evidence and Demo Lead).

Built from Tuhin's code, files, terminal output and commits. Where something can't be seen in the evidence, it says so rather than guessing. Exact times are in the GitHub commit history for the `cleaning-data` branch; commit references are given where known.

## Challenges solved

### 1. Hidden Mac files in the corpus zip
- **Challenge:** The supplied zip (`lynceus_main_0930.zip`) held 30 real case files plus 30 hidden Mac system files (`__MACOSX/._case-*.txt`). Loaded as-is, the tool would have treated them as 60 entries, half of them junk.
- **Fix:** Only the 30 real case files were placed in `Data/Original_data`; the hidden Mac files were left out. (The exact method isn't recorded in the code.)
- **Evidence:** `Data/Original_data` contains exactly 30 files; corpus build reports "Generated 30 corpus documents".
- **When:** corpus commit `7433b58`

### 2. Keeping the original corpus untouched
- **Challenge:** The rules say the corpus must not be edited by hand, but the text needed cleaning before search.
- **Fix:** Originals stay in `Data/Original_data`; the script writes cleaned copies to a separate `Data/Cleaned_data` folder and records a SHA-256 fingerprint of each file in `Data/manifest.csv`, so any change can be detected.
- **Evidence:** All 30 files in `Original_data` checked byte-for-byte against the supplied zip: identical.
- **When:** corpus commit `7433b58`

### 3. Hidden characters and formatting noise
- **Challenge:** Text files can carry invisible characters (such as a byte-order mark), inconsistent line endings and extra spaces that disrupt search.
- **Fix:** `scripts/data_cleaning.py` strips these out while keeping the original language, punctuation, numbers, company names and industry terms.
- **Result:** No noise was found: the cleaned copies of all 30 supplied files are identical to the originals. The step stays in as a safeguard for the live-round files. (The before-and-after example in Tuhin's README is an illustration, not a file from the corpus.)
- **When:** corpus commit `7433b58`

### 4. Answer key lists 39 files, corpus has 30
- **Challenge:** The answer key file map lists 39 case files, but only 30 were supplied.
- **Fix:** The script records the nine absent files in `Data/manifest.csv` as `missing_source` instead of creating placeholder entries, so nothing is invented.
- **Finding:** The nine are exactly the live-round cases (251, 281, 291, 419, 472, 570, 699, 985, 994). Two (251, 281) have since been released and loaded; see challenge 7.
- **When:** corpus commit `7433b58`

### 5. Garbled dash in the Johnson Controls delivery name
- **Challenge:** The terminal showed `â€“` instead of a dash (–) in "Johnson Controls – 175 ERPs to Two Cloud Platforms".
- **Fix:** None needed. `Data/manifest.csv` and Ashar's backend (11:56 screenshot) both show the dash correctly; the garbling was only how Windows PowerShell displayed the file.
- **When:** confirmed during the evidence check of commit `7433b58`

### 6. Getting the data to the rest of the team
- **Challenge:** The search and backend needed the corpus in a ready-to-use form.
- **Fix:** `scripts/build_corpus.py` turns the cleaned files and manifest into `Data/corpus.py`, one record per case (case ID, language, text, source file, delivery, round). Ashar's backend now serves these records at `/endpoints/documents`.
- **Evidence:** `evidence/screenshots/corpus_build.png`, `corpus_output.png`, `documents_api.png`
- **When:** before 11:56 (backend screenshot timestamp); corpus commit `7433b58`

### 7. First live-round files landed outside the repository
- **Challenge:** When the first two live-round files were released (case-251 and case-281), they were saved in the outer project folder on Tuhin's laptop, not in the repository's `Data/Original_data`, so the pipeline couldn't see them.
- **How it was found:** Tuhin's AI agent searched the project folders and found both files sitting one level above the repository.
- **Fix:** Copies of both files were placed in `Data/Original_data` (the outer copies were left untouched and the file contents were not edited), then the pipeline was rerun. Both new cases passed the quality checks. Committed and pushed as `6f550d8` ("Add newly released live cases") on the `cleaning-data` branch.
- **Result:** 32 source files, 32 cleaned files, 32 corpus documents; 7 live-round files still to be released.
- **Note for the live round write-up:** the files were moved into the right folder, not edited. To meet the brief's "no one touching them by hand", a better long-term fix is to let the pipeline pick up new files from wherever they are dropped (for example, a source-folder option on the run command).
- **Agent use:** this step was carried out by Tuhin's AI agent, which reported its commands and results in full. Tuhin's review to be recorded in the agent log.
- **Evidence:** `evidence/screenshots/live_files_pipeline_run.png`
- **When:** commit `6f550d8`

### 8. One command to run the whole pipeline
- **Challenge:** The pipeline needed two commands, and the first needed the answer key path typed in. The brief requires everything to run from a clean start with one command.
- **Fix:** New script `scripts/run_pipeline.py` runs cleaning and corpus building together: `py -3 scripts\run_pipeline.py`
- **Evidence:** `evidence/screenshots/live_files_pipeline_run.png`
- **When:** committed to `cleaning-data` before `6f550d8` (exact commit in branch history)

### 9. Live-round files looked like errors
- **Challenge:** The unreleased live-round files were labelled `missing_source`, which read like a data error.
- **Fix:** The pipeline now reports them separately as "Unreleased live files" (currently 7).
- **Evidence:** `evidence/screenshots/live_files_pipeline_run.png`
- **When:** committed to `cleaning-data` before `6f550d8` (exact commit in branch history)

## Open challenges

| # | Challenge | Proposed fix | Owner | Status |
|---|-----------|--------------|-------|--------|
| 10 | Two Japanese files (case-245, case-446) wrongly flagged as too short: the word counter splits on spaces, which Japanese doesn't use | Use character count for languages without spaces | Tuhin | ☐ Open (check latest quality report) |
| 11 | `language` and `delivery` fields are copied from the answer key, and the pipeline depends on it; Accenture won't have an answer key for real documents | Team decision: evaluation only, or keep and list as a limitation. Not yet decided. | Tuhin, Isabel | ☐ Open |
| 12 | Python temporary files (`__pycache__`) still tracked in the repo: the local folders were deleted, but the agent restored `scripts/__pycache__/data_cleaning.cpython-314.pyc` rather than removing it from Git | Add a `.gitignore` and remove the folder from Git | Tuhin | ☐ Open |
| 13 | Work is on the `cleaning-data` branch, not yet merged into main | Merge before 14:45 | Tuhin, Isabel | ☐ Open |
| 14 | New live-round files must be placed in `Data/Original_data` before the pipeline sees them | Let the run command take a source folder, or agree one drop folder for the remaining 7 files | Tuhin | ☐ Open |

## Questions for Tuhin

1. Were there any other problems you hit that aren't listed here?
2. How did you keep the hidden Mac files out?
3. Did you find any hidden characters or formatting noise in the files, or is the cleaning purely a safeguard?
4. Roughly what time did you solve each of the challenges above?
5. Did you review what your AI agent did when adding case-251 and case-281? (Needed for the agent log.)
