# Decisions log

Kept by Ahmad (Evidence and Demo Lead). One line per decision, problem or milestone, with the time and a "because" where there is one. Newest entries at the bottom.

## Log

**09:50 – Roles agreed.**
- Delivery Lead: Isabel
- Business Analysts: Abbas and Yurie
- Data Engineer: Tohin
- Search Engineer: Elakya
- Agent Engineers: Ashar and Javid
- Evaluation Lead: Girthan
- Evidence and Demo Lead: Ahmad

11:40 – Corpus loader working. Tuhin ran scripts/build_corpus.py, which generated 30 corpus documents (Data/corpus.py). Count matches the 30 case files, so the Mac junk files were skipped. Screenshot:<img width="1006" height="246" alt="image" src="https://github.com/user-attachments/assets/8bb10b90-94bf-4e7f-9748-db44d2b7b281" />

11:45 – Corpus record format confirmed. Each record has case ID, language, body text, source file, delivery name and round. Screenshot:11:45 – Corpus record format confirmed. Each record has case ID, language, body text, source file, delivery name and round. Screenshot: <img width="1290" height="643" alt="image" src="https://github.com/user-attachments/assets/7f1aba4c-5f60-47bf-a063-1caa9898861c" />

11:56 – Backend running. Ashar built the backend, which serves the corpus records from Tuhin’s pipeline (/endpoints/documents). Tuhin’s and Ashar’s work now connected. Screenshot: <img width="1490" height="749" alt="image" src="https://github.com/user-attachments/assets/50dd4012-e5d5-4c37-9873-212702f71311" />


**__:__ – Data issue found in corpus zip.** `lynceus_main_0930.zip` contains 30 case files plus 30 hidden Mac files (`__MACOSX/._case-*.txt`). The loader needs to skip these, because they are not real entries. Corpus not edited by hand.

**__:__ – Test set drafted by Abbas and Yurie.** 12 questions (6 sales lead, 6 delivery lead), including the 2 supplied sample questions. Covers: 2 cross-industry matches (S3 banking to fisheries, D1 food factory to mining), 2 non-English matches (S4 Portuguese, D5 Indonesian), 1 no-match question (D6 Mars spacecraft). Status: draft, awaiting product owner sign-off.

**__:__ – Test set approved by product owner.** Changes made: ________

**__:__ – Test set committed to repo** (commit: ________), before search build started.

<!-- Add new entries below. Template:
**HH:MM – What happened.** Who decided / found it. Because: ________
-->

## Check-in rounds

Every 30 minutes or so, ask each person: "What have you done since I last asked, and did you decide anything?"

| Time | Isabel | Abbas / Yurie | Tohin | Elakya | Ashar / Javid | Girthan |
|------|--------|---------------|-------|--------|---------------|---------|
|      |        |               |       |        |               |         |
|      |        |               |       |        |               |         |
|      |        |               |       |        |               |         |
|      |        |               |       |        |               |         |
