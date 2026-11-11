import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "case-001.txt").write_text(
        "A retailer's contact centre had long wait times. An AI assistant cut call handling.",
        encoding="utf-8")
    (corpus / "case-002.txt").write_text(
        "A legacy rule engine ran 2,000 data validation rules, refactored with generative AI.",
        encoding="utf-8")
    # BM25 needs more than two documents to give terms meaningful weight
    for n, text in enumerate(["Hospital records moved to the cloud.",
                              "A brewer merged its UK business with a pub operator.",
                              "An insurer digitised claims handling."], start=10):
        (corpus / f"case-0{n}.txt").write_text(text, encoding="utf-8")
    tests = tmp_path / "test_set.json"
    tests.write_text(json.dumps([
        {"id": "T1", "question": "rewrite legacy validation rules", "expected": ["case-002"]},
        {"id": "T2", "question": "florist wedding bouquets", "expected": []},
    ]), encoding="utf-8")

    from routers import search_api
    monkeypatch.setattr(search_api, "CORPUS_DIR", str(corpus))
    monkeypatch.setattr(search_api, "ENRICHED_DIR", str(tmp_path / "none"))
    monkeypatch.setattr(search_api, "TEST_SET", str(tests))
    monkeypatch.setenv("LYNCEUS_EMBEDDER", "none")
    monkeypatch.setitem(search_api._state, "index", None)
    app = FastAPI()
    app.include_router(search_api.router)
    return TestClient(app), corpus


def test_search_endpoint(client):
    c, _ = client
    r = c.get("/api/search", params={"q": "legacy validation rules", "k": 3}).json()
    assert r["results"][0]["case_id"] == "case-002"
    assert r["results"][0]["source_path"] == "/api/cases/case-002"
    assert r["results"][0]["why"]


def test_search_rejects_empty_query(client):
    c, _ = client
    assert c.get("/api/search", params={"q": ""}).status_code == 422


def test_cases_and_case_detail(client):
    c, _ = client
    assert {"case-001", "case-002"} <= {x["case_id"] for x in c.get("/api/cases").json()}
    d = c.get("/api/cases/case-002").json()
    assert "validation rules" in d["text"]
    assert c.get("/api/cases/case-404").status_code == 404


def test_similar_endpoint(client):
    c, _ = client
    r = c.get("/api/cases/case-001/similar", params={"k": 2}).json()
    assert len(r["results"]) == 2
    assert all(x["case_id"] != "case-001" for x in r["results"])
    assert c.get("/api/cases/case-404/similar").status_code == 404


def test_reindex_picks_up_new_file(client):
    c, corpus = client
    assert c.get("/api/status").json()["cases"] == 5
    (corpus / "case-003.txt").write_text("Satellites detect methane leaks.", encoding="utf-8")
    assert c.post("/api/reindex").json()["cases"] == 6


def test_evaluate_endpoint(client):
    c, _ = client
    r = c.get("/api/evaluate").json()
    assert r["total"] == 2 and r["hits"] == 2


def test_post_search_matches_frontend_contract(client):
    c, _ = client
    r = c.post("/api/search", json={"query": "legacy validation rules"}).json()
    top = r["results"][0]
    assert top["case_id"] == "case-002"
    # every field frontend/src/api/search.ts reads, plus the explanation
    for f in ("case_id", "source_path", "language", "sector", "country", "problem_plain",
              "capability", "scale_outcomes", "reusable", "summary", "why", "strong_match"):
        assert f in top
    assert "message" in r


def test_post_search_no_match_sets_message(client):
    c, _ = client
    r = c.post("/api/search", json={"query": "florist wedding bouquets"}).json()
    assert r["no_strong_match"] is True
    assert r["message"].startswith("No strong match")
    assert all(x["strong_match"] is False for x in r["results"])


def test_post_search_validates_body(client):
    c, _ = client
    assert c.post("/api/search", json={"query": ""}).status_code == 422
    assert c.post("/api/search", json={}).status_code == 422