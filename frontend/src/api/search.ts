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

  await new Promise((resolve) => setTimeout(resolve, 700));

  if (query.trim().toLowerCase() === "error") {
    throw new Error("Example error: search is unavailable.");
  }

  if (query.trim().toLowerCase() === "none") {
    return {
      results: [],
      message: "No strong match found.",
    };
  }

  return {
    results: [
      {
        case_id: "mock-case",
        source_path: "Mock source — not a real file",
        language: "English",
        sector: "Example sector",
        country: "Example location",
        problem_plain: "Placeholder description of a client problem.",
        capability: "Placeholder technique used.",
        scale_outcomes: "No real figures — mock data.",
        reusable: "Placeholder reusable approach.",
        summary:
          "This is a mock project record. Real content will come from the backend.",
      },
    ],
    message: null,
  };
}
