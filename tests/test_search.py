import json
from pathlib import Path

import pytest

from backend.search import LynceusIndex, load_field_map, load_records, tokenize

EXPECTED_KEYS = {"rank", "case_id", "score", "similarity", "strong_match",
                 "summary", "why", "source"}


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


@pytest.fixture
def corpus(tmp_path):
    c = tmp_path / "corpus"
    write(c / "case-001.txt",
          "A retailer's contact centre had long wait times. An AI virtual assistant "
          "and agent assist tools cut call handling effort.")
    write(c / "case-002.txt",
          "A regulator's legacy rule engine ran 2,000 data validation rules. "
          "A generative AI tool refactored each rule in about a minute.")
    write(c / "case-003.txt",
          "Die Versicherung musste ihre IKT-Governance an DORA anpassen.")
    # Mac zip junk that must never be indexed
    write(c / "__MACOSX" / "._case-001.txt", "\x00\x05junk")
    write(c / "._case-002.txt", "junk")
    return c


@pytest.fixture
def enriched(tmp_path):
    e = tmp_path / "enriched"
    write(e / "case-003.json", json.dumps({
        "case_id": "case-003",
        "language": "German",
        "sector": "Insurance",
        "problem_plain": "An insurer had to align IT risk management with the EU DORA regulation.",
        "capability": "Gap analysis and compliance roadmap",
    }))
    return e


def build(corpus, enriched=None, field_map=None):
    return LynceusIndex(load_records(str(corpus), str(enriched) if enriched else None,
                                     field_map), embedder=None)


# loading

def test_junk_files_skipped(corpus):
    ids = {r.case_id for r in load_records(str(corpus))}
    assert ids == {"case-001", "case-002", "case-003"}


def test_unenriched_cases_still_indexed(corpus, enriched):
    recs = {r.case_id: r for r in load_records(str(corpus), str(enriched))}
    assert len(recs) == 3
    assert recs["case-003"].fields["sector"] == "Insurance"
    assert recs["case-001"].fields == {}  # falls back to raw text


def test_bad_enrichment_json_is_skipped(corpus, enriched):
    write(enriched / "case-001.json", "{not valid json")
    recs = {r.case_id: r for r in load_records(str(corpus), str(enriched))}
    assert recs["case-001"].fields == {}
    assert recs["case-003"].fields  # good file still loads


def test_field_map_renames_their_fields(corpus, tmp_path):
    e = tmp_path / "enriched_theirs"
    write(e / "case-003.json", json.dumps({
        "case_id": "case-003",
        "client_problem": "An insurer needed EU DORA compliance for IT risk.",
        "technique": ["gap analysis", "roadmap"],
    }))
    fmap_path = tmp_path / "field_map.json"
    write(fmap_path, json.dumps({"problem_plain": "client_problem", "capability": "technique"}))
    recs = {r.case_id: r for r in load_records(str(corpus), str(e), load_field_map(str(fmap_path)))}
    assert "DORA" in recs["case-003"].fields["problem_plain"]
    assert recs["case-003"].fields["capability"] == "gap analysis roadmap"


def test_missing_field_map_is_fine():
    assert load_field_map("does-not-exist.json") == {}


def test_empty_corpus_raises(tmp_path):
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError):
        build(tmp_path / "empty")


# search

def test_output_format(corpus):
    out = build(corpus).search("contact centre wait times", k=3)
    assert {"query", "no_strong_match", "top_strength", "embedder", "results"} <= out.keys()
    assert out["results"] and EXPECTED_KEYS <= out["results"][0].keys()


def test_cross_vocabulary_match(corpus):
    out = build(corpus).search("bank rewriting thousands of legacy validation rules", k=3)
    assert out["results"][0]["case_id"] == "case-002"


def test_cross_language_via_enrichment(corpus, enriched):
    # Source is German; only the English enrichment can make this match
    out = build(corpus, enriched).search("insurer EU DORA IT risk compliance", k=3)
    top = out["results"][0]
    assert top["case_id"] == "case-003"
    assert "German" in top["why"]


def test_cross_language_fails_without_enrichment(corpus):
    # Documents the known limitation: BM25 alone cannot bridge languages
    out = build(corpus).search("insurer IT risk compliance", k=3)
    assert all(r["case_id"] != "case-003" for r in out["results"] if r["strong_match"])


def test_no_match_does_not_pad(corpus):
    out = build(corpus).search("florist choosing wedding bouquets", k=5)
    assert out["no_strong_match"] is True
    assert len(out["results"]) <= 2


def test_new_live_round_file_is_picked_up(corpus):
    # Simulates the 12:30 drop: add a file, rebuild, it is searchable
    write(corpus / "case-999.txt",
          "Satellite data and ground sensors detect methane leaks in a gas network.")
    out = build(corpus).search("water company finding pipe leaks with sensors", k=3)
    assert out["results"][0]["case_id"] == "case-999"


def test_summary_is_source_text_not_generated(corpus):
    out = build(corpus).search("contact centre wait times", k=1)
    r = out["results"][0]
    source = Path(r["source"]).read_text(encoding="utf-8")
    assert r["summary"] in source  # traceable verbatim


def test_tokenizer_normalises_plurals():
    assert tokenize("rules centres companies boxes") == ["rule", "centre", "company", "box"]


# embedder calls

class CountingEmbedder:
    """Stands in for Voyage: deterministic vectors, counts API calls."""
    name = "fake"

    def __init__(self):
        self.calls = 0

    def embed(self, texts, kind):
        import numpy as np
        self.calls += 1
        rng = [np.random.default_rng(abs(hash(t)) % 2**32).standard_normal(16) for t in texts]
        return np.array(rng, dtype=np.float32)


def test_embeddings_are_cached_and_queries_batched(corpus, tmp_path, monkeypatch):
    from backend import search
    monkeypatch.setattr(search, "CACHE_DIR", tmp_path / "cache")
    emb = CountingEmbedder()
    idx = LynceusIndex(load_records(str(corpus)), emb)
    assert emb.calls == 1                      # corpus embedded once

    qs = ["contact centre wait times", "legacy validation rules", "florist bouquets"]
    idx.prime_queries(qs)
    assert emb.calls == 2                      # all questions in one call
    for q in qs:
        idx.search(q)
    assert emb.calls == 2                      # searches reuse cached query vectors

    LynceusIndex(load_records(str(corpus)), emb).search(qs[0])
    assert emb.calls == 2                      # rebuild and re-search hit the disk cache


def test_new_file_embeds_only_the_new_text(corpus, tmp_path, monkeypatch):
    from backend import search

    class TextCounter(CountingEmbedder):
        def __init__(self):
            super().__init__()
            self.texts = 0

        def embed(self, texts, kind):
            self.texts += len(texts)
            return super().embed(texts, kind)

    monkeypatch.setattr(search, "CACHE_DIR", tmp_path / "cache")
    emb = TextCounter()
    LynceusIndex(load_records(str(corpus)), emb)
    assert emb.texts == 3

    write(corpus / "case-999.txt", "Satellite data detects methane leaks in a gas network.")
    LynceusIndex(load_records(str(corpus)), emb)   # simulates /reindex at 12:30
    assert emb.texts == 4                          # only the new case was embedded


# fuzzy + similar

def test_fuzzy_corrects_typos(corpus):
    out = build(corpus).search("legacy validaton rulez", k=3)
    assert out["corrections"] == {"validaton": "validation", "rulez": "rule"}
    assert out["results"][0]["case_id"] == "case-002"


def test_fuzzy_leaves_short_and_known_words_alone(corpus):
    out = build(corpus).search("AI rules", k=3)
    assert out["corrections"] == {}


def test_fuzzy_does_not_invent_matches(corpus):
    out = build(corpus).search("florist choosing wedding bouquets", k=3)
    assert out["no_strong_match"] is True


def test_similar_cases(corpus):
    out = build(corpus).similar("case-001", k=2)
    assert out["case_id"] == "case-001"
    assert all(r["case_id"] != "case-001" for r in out["results"])
    with pytest.raises(KeyError):
        build(corpus).similar("case-404")
