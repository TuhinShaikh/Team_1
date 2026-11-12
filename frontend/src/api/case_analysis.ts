export type CaseAnalysis = {
  analysis: {
    Observations: string[];
    OverallAssesment: string[];
  };
  input_tokens: number;
  output_tokens: number;
  stop_reason: string;
  analysis_source?: "anthropic" | "saved_enrichment" | "source_text";
  reviewed_by_human?: boolean | null;
};

export async function analyseCase(caseId: string): Promise<CaseAnalysis> {
  const normalizedId = caseId.trim().replace(/[‐‑‒–—―−]/g, "-");
  const response = await fetch(
    `http://localhost:8000/endpoints/${encodeURIComponent(normalizedId)}`
  );

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`No case found with ID “${normalizedId}”.`);
    }
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Case analysis failed (${response.status}).`);
  }

  return response.json();
}
