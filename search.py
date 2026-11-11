"""Lynceus search: hybrid BM25 + embeddings over enriched case records.

Usage:
    python search.py "a client wants to cut call-centre wait times with AI"
    python search.py --raw data/corpus --enriched data/enriched "query"
    python search.py --json "query"                      # agreed output format
    python search.py --calibrate evaluation/test_set.json
    python search.py                                     # interactive prompt

Every case file in --raw is indexed. Enrichment is attached where it exists;
cases without it fall back to raw text. Map the enrichment's field names to
ours in field_map.json if they differ.

Design:
    - BM25 over the English enriched fields (exact terms: SAP, DORA, call centre...)
    - Embeddings over problem + capability (meaning across vocabularies),
      plus the raw source text as a multilingual fallback
    - Reciprocal Rank Fusion to combine rankings
    - No-match gate on the best absolute similarity (RRF is rank-only)
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

# ---------------------------------------------------------------- config

RRF_K = 60                 # standard RRF constant
CANDIDATES = 10            # top-N taken from each retriever before fusion
COS_THRESHOLD = 0.35       # CALIBRATE on your test set (see calibrate())
BM25_THRESHOLD = 4.0       # used only when no embedder is available
FUZZY_CUTOFF = 0.85        # difflib similarity needed to correct a query typo
FUZZY_MIN_LEN = 5          # don't "correct" short words (too many false fixes)
CACHE_DIR = Path(".cache/embeddings")

# Fields from the agreed enrichment schema. Update if the schema changes.
TEXT_FIELDS = ["sector", "country", "problem_plain", "capability",
               "scale_outcomes", "reusable"]
SEMANTIC_FIELDS = ["problem_plain", "capability"]

STOPWORDS = set("""a an the and or of to in on for with by from at as is are was were be
been it its this that these those we our you your they their client clients wants want
needs need help helping how what which who can could would should into over about using
use used new across more than""".split())


# ---------------------------------------------------------------- records

@dataclass
class Record:
    case_id: str
    source_path: str
    raw_text: str
    fields: dict = field(default_factory=dict)

    def field_text(self, names: list[str]) -> str:
        parts = []
        for n in names:
            v = self.fields.get(n)
            if isinstance(v, list):
                v = " ".join(map(str, v))
            if v:
                parts.append(str(v))
        return " ".join(parts)


def _is_junk(p: Path) -> bool:
    return "__MACOSX" in p.parts or p.name.startswith("._") or p.name.startswith(".")


def load_field_map(path: str | None) -> dict:
    """Optional JSON mapping OUR field name -> THEIR field name, e.g.
    {"problem_plain": "client_problem", "scale_outcomes": "figures"}.
    Lets the agent engineer's schema plug in without code changes."""
    if path and Path(path).exists():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return {}


def _flatten(v):
    if isinstance(v, dict):
        return " ".join(f"{k}: {_flatten(x)}" for k, x in v.items())
    if isinstance(v, list):
        return " ".join(_flatten(x) for x in v)
    return "" if v is None else str(v)


def load_records(corpus_dir: str, enriched_dir: str | None = None,
                 field_map: dict | None = None) -> list[Record]:
    """The corpus folder is the source of truth: every case file is indexed.
    Enrichment is attached where a matching JSON exists (by case_id or file
    stem); cases without enrichment fall back to raw text, so a new live-round
    file is searchable even before it has been enriched."""
    field_map = field_map or {}
    enrich: dict[str, dict] = {}
    if enriched_dir and Path(enriched_dir).exists():
        for p in sorted(Path(enriched_dir).glob("*.json")):
            if _is_junk(p):
                continue
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"[search] skipping bad enrichment {p.name}: {e}")
                continue
            mapped = {ours: _flatten(d.get(theirs)) for ours, theirs in field_map.items()}
            mapped.update({k: _flatten(v) for k, v in d.items() if k not in mapped})
            cid = Path(str(d.get("case_id") or p.stem)).stem
            enrich[cid] = mapped

    recs = []
    for p in sorted(Path(corpus_dir).rglob("*.txt")):
        if _is_junk(p):
            continue
        text = p.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            print(f"[search] empty file skipped: {p.name}")
            continue
        recs.append(Record(case_id=p.stem, source_path=str(p), raw_text=text,
                           fields=enrich.get(p.stem, {})))

    missing = [r.case_id for r in recs if not r.fields]
    if enrich and missing:
        print(f"[search] {len(missing)} case(s) not enriched, using raw text: {', '.join(missing)}")
    orphans = set(enrich) - {r.case_id for r in recs}
    if orphans:
        print(f"[search] enrichment with no source file (ignored): {', '.join(sorted(orphans))}")
    return recs


# ---------------------------------------------------------------- text

def tokenize(text: str) -> list[str]:
    toks = re.findall(r"\w+", text.lower())
    out = []
    for t in toks:
        if t in STOPWORDS or len(t) < 2:
            continue
        # light normalisation so "centres"/"centre", "rules"/"rule" meet
        if len(t) > 4:
            if t.endswith("ies"):
                t = t[:-3] + "y"
            elif re.search(r"(ss|x|z|ch|sh)es$", t):
                t = t[:-2]
            elif t.endswith("s") and not t.endswith("ss"):
                t = t[:-1]
        out.append(t)
    return out


def first_sentences(text: str, n: int = 2) -> str:
    sents = re.split(r"(?<=[.!?。])\s+", text.strip())
    return " ".join(sents[:n])


# ---------------------------------------------------------------- embedders

class Embedder:
    name = "none"

    def embed(self, texts: list[str], kind: str) -> np.ndarray:  # kind: "document" | "query"
        raise NotImplementedError


class VoyageEmbedder(Embedder):
    """Multilingual. Needs VOYAGE_API_KEY and the voyageai package.

    Free tier (no payment method) allows 3 requests/min and 10K tokens/min, so
    texts are sent in small batches with a minimum gap between calls. Once a
    payment method is added, set VOYAGE_MIN_INTERVAL=0 to remove the wait."""

    def __init__(self, model: str | None = None):
        import voyageai
        self.model = model or os.getenv("VOYAGE_MODEL", "voyage-3-lite")
        self.client = voyageai.Client(max_retries=3)
        self.name = f"voyage:{self.model}"
        self.batch_size = int(os.getenv("VOYAGE_BATCH_SIZE", "8"))
        self.min_interval = float(os.getenv("VOYAGE_MIN_INTERVAL", "21"))
        self._last_call = 0.0

    def _throttle(self):
        wait = self._last_call + self.min_interval - time.monotonic()
        if wait > 0:
            print(f"[search] Voyage free-tier limit: waiting {wait:.0f}s")
            time.sleep(wait)
        self._last_call = time.monotonic()

    def embed(self, texts, kind):
        out = []
        for start in range(0, len(texts), self.batch_size):
            self._throttle()
            r = self.client.embed(texts[start:start + self.batch_size],
                                  model=self.model, input_type=kind)
            out.extend(r.embeddings)
        return np.array(out, dtype=np.float32)


class LocalEmbedder(Embedder):
    """Offline fallback. Needs sentence-transformers and the model downloaded."""

    def __init__(self, model: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        from sentence_transformers import SentenceTransformer
        self.m = SentenceTransformer(model)
        self.name = f"local:{model}"

    def embed(self, texts, kind):
        return np.asarray(self.m.encode(texts, normalize_embeddings=True), dtype=np.float32)


def get_embedder(prefer: str = "auto") -> Embedder | None:
    tries = {"voyage": [VoyageEmbedder], "local": [LocalEmbedder],
             "auto": [VoyageEmbedder, LocalEmbedder], "none": []}[prefer]
    if prefer in ("auto", "voyage") and not os.getenv("VOYAGE_API_KEY"):
        tries = [t for t in tries if t is not VoyageEmbedder]
    for cls in tries:
        try:
            return cls()
        except Exception as e:  # missing package / model / key
            print(f"[search] {cls.__name__} unavailable: {e}")
    print("[search] no embedder: running BM25 only (non-English entries will be weak)")
    return None


def _normalise(m: np.ndarray) -> np.ndarray:
    return m / np.clip(np.linalg.norm(m, axis=1, keepdims=True), 1e-9, None)


def _doc_file(emb: Embedder, text: str) -> Path:
    key = hashlib.sha1((emb.name + "\x00doc\x00" + text).encode()).hexdigest()[:16]
    return CACHE_DIR / f"d_{key}.npy"


def cached_embed(emb: Embedder, texts: list[str]) -> np.ndarray:
    """Per-document disk cache: only texts never seen before are sent to the
    embedder, so adding live-round files (or reindexing) embeds just the new ones."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    files = [_doc_file(emb, t) for t in texts]
    todo = [i for i, f in enumerate(files) if not f.exists()]
    if todo:
        print(f"[search] embedding {len(todo)} new text(s) with {emb.name}")
        vecs = _normalise(emb.embed([texts[i] for i in todo], "document"))
        for i, v in zip(todo, vecs):
            np.save(files[i], v)
    return np.stack([np.load(f) for f in files])


# ---------------------------------------------------------------- index

class LynceusIndex:
    def __init__(self, records: list[Record], embedder: Embedder | None):
        self.records = records
        self.embedder = embedder
        if not records:
            raise ValueError("No case files found. Check the --raw corpus path.")

        # BM25 per record: enriched English fields if present, else raw text
        self.bm25_docs = [tokenize(r.field_text(TEXT_FIELDS) or r.raw_text) for r in records]
        self.bm25 = BM25Okapi(self.bm25_docs)
        self.vocab = sorted({t for doc in self.bm25_docs for t in doc})
        self._vocab_set = set(self.vocab)

        self.sem = self.raw = None
        if embedder:
            if any(r.fields for r in records):
                self.sem = cached_embed(embedder, [r.field_text(SEMANTIC_FIELDS) or r.raw_text
                                                   for r in records])
            self.raw = cached_embed(embedder, [r.raw_text for r in records])

    # -- query embeddings, cached on disk so repeat questions cost no API calls
    def _qfile(self, q: str) -> Path:
        key = hashlib.sha1((self.embedder.name + "\x00" + q).encode()).hexdigest()[:16]
        return CACHE_DIR / f"q_{key}.npy"

    def prime_queries(self, queries: list[str]) -> None:
        """Embed all uncached queries in one batched call (used by --calibrate)."""
        if not self.embedder:
            return
        todo = [q for q in dict.fromkeys(queries) if not self._qfile(q).exists()]
        if todo:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            for q, v in zip(todo, _normalise(self.embedder.embed(todo, "query"))):
                np.save(self._qfile(q), v)

    def _query_vec(self, q: str) -> np.ndarray:
        f = self._qfile(q)
        if not f.exists():
            self.prime_queries([q])
        return np.load(f)

    # -- retrievers return {doc_index: score}
    def _fuzzy(self, toks: list[str]) -> tuple[list[str], dict[str, str]]:
        """Typo tolerance for keyword search: a query word that isn't in the
        index is swapped for its closest indexed word (e.g. 'validaton' ->
        'validation'). Embeddings already tolerate typos, so this only
        affects BM25. Corrections are returned so the UI can show them."""
        out, fixes = [], {}
        for t in toks:
            if t in self._vocab_set or len(t) < FUZZY_MIN_LEN or t.isdigit():
                out.append(t)
                continue
            m = difflib.get_close_matches(t, self.vocab, n=1, cutoff=FUZZY_CUTOFF)
            if m:
                fixes[t] = m[0]
                out.append(m[0])
            else:
                out.append(t)
        return out, fixes

    def similar(self, case_id: str, k: int = 5) -> dict:
        """'More like this': cases closest to a given case. Uses embeddings
        when available, otherwise the case's own text as a keyword query."""
        ids = [r.case_id for r in self.records]
        if case_id not in ids:
            raise KeyError(case_id)
        i = ids.index(case_id)
        mat = self.sem if self.sem is not None else self.raw
        if mat is not None:
            scores = mat @ mat[i]
            method = "embedding similarity"
        else:
            scores = self.bm25.get_scores(self.bm25_docs[i])
            method = "keyword overlap"
        order = [j for j in np.argsort(-scores) if j != i][:k]
        return {"case_id": case_id, "method": method, "results": [
            {"rank": n, "case_id": self.records[j].case_id,
             "score": round(float(scores[j]), 3),
             "summary": self._summary(self.records[j]),
             "source": self.records[j].source_path}
            for n, j in enumerate(order, 1)]}

    def _bm25(self, q_toks):
        s = self.bm25.get_scores(q_toks)
        top = np.argsort(-s)[:CANDIDATES]
        return {int(i): float(s[i]) for i in top if s[i] > 0}

    def _dense(self, qv, mat):
        s = mat @ qv
        top = np.argsort(-s)[:CANDIDATES]
        return {int(i): float(s[i]) for i in top}

    def search(self, query: str, k: int = 5) -> dict:
        q_toks, corrections = self._fuzzy(tokenize(query))
        rankings: dict[str, dict[int, float]] = {"bm25": self._bm25(q_toks)}
        if self.embedder:
            qv = self._query_vec(query)
            if self.sem is not None:
                rankings["semantic"] = self._dense(qv, self.sem)
            rankings["raw_multilingual"] = self._dense(qv, self.raw)

        # Reciprocal Rank Fusion
        fused: dict[int, float] = {}
        for scores in rankings.values():
            for rank, i in enumerate(sorted(scores, key=scores.get, reverse=True)):
                fused[i] = fused.get(i, 0.0) + 1.0 / (RRF_K + rank + 1)
        order = sorted(fused, key=fused.get, reverse=True)[:k]

        # No-match gate on absolute similarity
        def best_cos(i):
            vals = [rankings[n].get(i) for n in ("semantic", "raw_multilingual") if n in rankings]
            vals = [v for v in vals if v is not None]
            return max(vals) if vals else None

        if self.embedder:
            top_strength = max((best_cos(i) or 0.0) for i in order) if order else 0.0
            no_strong = top_strength < COS_THRESHOLD
        else:
            top_strength = max(rankings["bm25"].values(), default=0.0)
            no_strong = top_strength < BM25_THRESHOLD

        results = []
        for rank, i in enumerate(order, 1):
            r = self.records[i]
            cos = best_cos(i)
            strong = (cos is not None and cos >= COS_THRESHOLD) or (
                not self.embedder and rankings["bm25"].get(i, 0) >= BM25_THRESHOLD)
            results.append({
                "rank": rank,
                "case_id": r.case_id,
                "score": round(fused[i], 4),
                "similarity": None if cos is None else round(cos, 3),
                "strong_match": bool(strong),
                "summary": self._summary(r),
                "why": self._why(r, i, q_toks, rankings),
                "source": r.source_path,
            })

        if no_strong:
            results = results[:2]  # show closest only, labelled weak; don't pad

        return {"query": query, "corrections": corrections, "no_strong_match": no_strong,
                "top_strength": round(float(top_strength), 3),
                "embedder": self.embedder.name if self.embedder else "none",
                "results": results}

    # -- explanation and summary
    def _summary(self, r: Record) -> str:
        # Agent engineer's grounded 2-sentence summary if present; otherwise
        # fall back to source-traceable text (never generated here).
        return r.fields.get("summary") or first_sentences(
            r.fields.get("problem_plain") or r.raw_text, 2)

    def _why(self, r: Record, i: int, q_toks, rankings) -> str:
        reasons = []
        if r.fields:
            hits = {}
            qset = set(q_toks)
            for f in TEXT_FIELDS:
                overlap = qset & set(tokenize(r.field_text([f])))
                if overlap:
                    hits[f] = sorted(overlap)
            if hits:
                reasons.append("Matched terms: " + "; ".join(
                    f"{f} ({', '.join(t)})" for f, t in hits.items()))
        else:
            overlap = sorted(set(q_toks) & set(self.bm25_docs[i]))
            if overlap:
                reasons.append("Matched terms: " + ", ".join(overlap))

        if "semantic" in rankings and i in rankings["semantic"]:
            reasons.append(f"Similar problem (sim {rankings['semantic'][i]:.2f}): "
                           f"\"{first_sentences(r.fields.get('problem_plain', ''), 1)}\"")
        elif "raw_multilingual" in rankings and i in rankings["raw_multilingual"]:
            reasons.append(f"Semantic match on source text (sim {rankings['raw_multilingual'][i]:.2f})")

        lang = r.fields.get("language")
        if lang and str(lang).lower() not in ("english", "en"):
            reasons.append(f"Source in {lang}, matched via English enrichment")
        return " | ".join(reasons) or "Weak lexical/semantic overlap only"


# ---------------------------------------------------------------- calibration

def calibrate(index: LynceusIndex, test_set: list[dict], k: int = 3) -> None:
    """For each question: top-k hit, where each expected case landed, and the
    top strength. Use the strengths of answerable vs no-match questions to
    pick the threshold in the gap.
    test_set items: {"id", "question", "expected": [case_ids]} (empty = no match)."""
    index.prime_queries([t["question"] for t in test_set])
    hits = total = 0
    print(f"{'id':4} {'hit':5} {'strength':8} {'no_strong':9} {'expected (rank)':28} top-{k}")
    for t in test_set:
        out = index.search(t["question"], k=k)
        got = [r["case_id"] for r in out["results"]]
        if t["expected"]:
            ranks = {e: (got.index(e) + 1 if e in got else None) for e in t["expected"]}
            ok = all(v is not None for v in ranks.values())
            exp = ", ".join(f"{e}({v or '-'})" for e, v in ranks.items())
        else:
            ok = out["no_strong_match"]
            exp = "NO MATCH expected"
        hits += ok
        total += 1
        print(f"{t.get('id', '?'):4} {'✓' if ok else '✗':5} {out['top_strength']:<8.3f} "
              f"{str(out['no_strong_match']):9} {exp:28} {', '.join(got)}")
    print(f"\nTop-{k} hit rate: {hits}/{total} = {hits / total:.0%}   [embedder: {out['embedder']}]")


# ---------------------------------------------------------------- CLI

def build_index(args) -> LynceusIndex:
    recs = load_records(args.raw, args.enriched, load_field_map(args.field_map))
    return LynceusIndex(recs, get_embedder(args.embedder))


def print_results(out: dict) -> None:
    print(f"\nQuery: {out['query']}   [embedder: {out['embedder']}]")
    if out.get("corrections"):
        print("Spelling corrected: " + ", ".join(f"{a} → {b}" for a, b in out["corrections"].items()))
    if out["no_strong_match"]:
        print(f"⚠  No strong match found (best similarity {out['top_strength']}). "
              "Closest entries, shown as weak:\n")
    for r in out["results"]:
        tag = "" if r["strong_match"] else "  (weak)"
        print(f"{r['rank']}. {r['case_id']}{tag}   score={r['score']}  sim={r['similarity']}")
        print(f"   {r['summary']}")
        print(f"   Why: {r['why']}")
        print(f"   Source: {r['source']}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--raw", default="data/corpus", help="folder of case-*.txt")
    ap.add_argument("--enriched", default="data/enriched", help="folder of enriched JSON records")
    ap.add_argument("--field-map", default="field_map.json",
                    help="optional JSON mapping our field names to the enrichment's")
    ap.add_argument("--embedder", default="auto", choices=["auto", "voyage", "local", "none"])
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--json", action="store_true", help="print raw JSON (for the evaluator)")
    ap.add_argument("--calibrate", help="path to test set JSON")
    args = ap.parse_args()

    index = build_index(args)
    if args.calibrate:
        calibrate(index, json.loads(Path(args.calibrate).read_text()))
        return
    queries = [args.query] if args.query else iter(lambda: input("\nlynceus> ").strip(), "")
    for q in queries:
        out = index.search(q, k=args.k)
        print(json.dumps(out, indent=2, ensure_ascii=False) if args.json else "", end="")
        if not args.json:
            print_results(out)


if __name__ == "__main__":
    main()
