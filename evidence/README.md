# Lynceus: evidence pack

Team: Isabel, Abbas, Yurie, Tohin, Elakya, Ashar, Javid, Girthan, Ahmad

## How it works

<!-- 3–5 sentences: how the corpus is loaded, how the agent enriches each entry, how search ranks results, how it explains matches and how it decides nothing fits. Fill in from the decisions log. -->

## What we chose not to do, and why

<!-- Pull every "we decided not to… because…" line from the decisions log. -->

## Known limitations

<!-- Weaknesses found in testing and in the live round, and how we'd fix each properly. -->

## What it would take to put this in front of Accenture's sales and delivery teams

<!-- E.g. more entries, keeping enrichment up to date, human review at scale, confidentiality checks before anything reaches a client. -->

## Evidence index

| Evidence | Owner | Where | Done? |
|----------|-------|-------|-------|
| Test set (written before build) | Abbas and Yurie | ________ | ☐ |
| Product owner sign-off on test set | Abbas and Yurie | decisions_log.md | ☐ |
| Enriched corpus: agent draft and corrected version side by side (10+ records checked) | Ashar and Javid | ________ | ☐ |
| Agent log: skill, model, prompt, output, what a person changed | Ashar and Javid | ________ | ☐ |
| Evaluation score (right entry in top 3) and every miss explained | Girthan | ________ | ☐ |
| Live round results: returned, why, right or not, how checked, cause of any miss, new entries loaded untouched | Isabel and Girthan | ________ | ☐ |
| Client-ready note: agent draft, human edits, claim tracing, confidential flags (stretch) | ________ | ________ | ☐ |
| Clean-start run output | Tohin | ________ | ☐ |
| Decisions log | Ahmad | decisions_log.md | ☐ |
| Demo plan | Ahmad | demo_plan.md | ☐ |

## Test set coverage

| Brief requirement | Our questions |
|-------------------|---------------|
| At least 10 questions | 12 (S1–S6, D1–D6) |
| At least 2 matching another industry's vocabulary | S3 (bank → fisheries), D1 (food factory → mining) |
| At least 1 matching an entry not in English | S4 (Portuguese), D5 (Indonesian) |
| At least 1 where nothing fits | D6 (Mars spacecraft) |
