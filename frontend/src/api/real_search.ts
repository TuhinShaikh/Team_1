export type SearchResult = {
  case_id: string;
  source_path: string;
  language: string;
  summary: string;
  body: string;
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

  const response = await fetch("http://localhost:8000/endpoints/search", {
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
