"""Local full-text search over the generated case corpus."""

from __future__ import annotations

import math
import re
from collections import Counter

from corpus import DOCUMENTS


_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "how", "i", "in", "is", "it", "of", "on", "or", "that", "the",
    "their", "this", "to", "was", "were", "what", "with", "would",
}


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in _TOKEN_RE.findall(text.casefold())
        if len(token) > 1 and token not in _STOP_WORDS
    ]


def search_cases(query: str, limit: int = 5) -> dict:
    """Rank corpus documents using BM25 and return the best matching cases."""
    terms = _tokens(query)
    if not terms:
        return {"results": [], "message": "Add a few details about the client’s challenge."}

    documents = []
    for case in DOCUMENTS:
        searchable = f"{case.get('delivery', '')} {case.get('body', '')}"
        tokens = _tokens(searchable)
        documents.append((case, tokens, Counter(tokens)))

    count = len(documents)
    average_length = sum(len(tokens) for _, tokens, _ in documents) / max(count, 1)
    term_frequency = Counter(
        term
        for term in set(terms)
        for _, _, frequencies in documents
        if frequencies[term]
    )

    ranked = []
    for case, tokens, frequencies in documents:
        score = 0.0
        for term in set(terms):
            frequency = frequencies[term]
            if not frequency:
                continue
            inverse_document_frequency = math.log(
                1 + (count - term_frequency[term] + 0.5) / (term_frequency[term] + 0.5)
            )
            length_normalizer = 1.2 * (0.25 + 0.75 * len(tokens) / max(average_length, 1))
            score += inverse_document_frequency * frequency * 2.2 / (frequency + length_normalizer)

        if score:
            # Give exact phrase matches a modest boost while retaining BM25 ranking.
            haystack = f"{case.get('delivery', '')} {case.get('body', '')}".casefold()
            normalized_query = " ".join(terms)
            if normalized_query and normalized_query in haystack:
                score *= 1.25
            ranked.append((score, case))

    ranked.sort(key=lambda item: item[0], reverse=True)
    results = [
        {
            "case_id": case["case_id"],
            "source_path": case.get("document", case["case_id"]),
            "language": case.get("language", ""),
            "summary": case.get("delivery", ""),
            "body": case.get("body", ""),
        }
        for _, case in ranked[:limit]
    ]
    return {
        "results": results,
        "message": None if results else "No matching cases found. Try different terms.",
    }
