export type SearchResult = {
  case_id: string;
  enriched: boolean;
  reviewed_by_human: boolean;
  rank: number;
  score: number;
  similarity: number | null;
  strong_match: boolean;
  why: string;
  source_path: string;
  source_file: string;
  language: string;
  sector: string;
  country: string;
  problem_plain: string;
  capability: string;
  scale_outcomes: string;
  reusable: string;
  summary: string;
};

export type SearchResponse = {
  query: string;
  results: SearchResult[];
  message: string | null;
  no_strong_match: boolean;
  corrections: Record<string, string>;
  embedder: string;
};

export type ReindexResponse = {
  cases: number;
  enriched: number;
  embedder: string;
};

export async function searchCases(
  query: string
): Promise<SearchResponse> {
  if (!query.trim()) {
    throw new Error("Please describe the client's problem.");
  }

  const response = await fetch("http://localhost:8000/api/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query: query.trim() }),
  });

  if (!response.ok) {
    throw new Error(`Search failed (${response.status}).`);
  }

  return await response.json();
}

export async function reloadSearchIndex(): Promise<ReindexResponse> {
  const response = await fetch("http://localhost:8000/api/reindex", { method: "POST" });
  if (!response.ok) {
    throw new Error(`Could not reload case records (${response.status}).`);
  }
  return response.json();
}
