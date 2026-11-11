export async function searchCases(
  query: string
): Promise<SearchResponse> {
  if (!query.trim()) {
    throw new Error("Please describe the client's problem.");
  }

  // Example URL — replace with your teammate's actual endpoint.
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
} """