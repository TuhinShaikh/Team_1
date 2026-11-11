export type SearchResult = {
  case_id: string;
  source_path: string;
  language: string;
  sector: string;
  country: string;
  problem_plain: string;
  capability: string;
  scale_outcomes: string;
  reusable: string;
  summary?: string;
};

export type SearchResponse = {
  results: SearchResult[];
  message: string | null;
};

export async function searchCases(
  query: string
): Promise<SearchResponse> {
  if (!query.trim()) {
    throw new Error("Please describe the client's problem.");
  }

  // Example URL
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