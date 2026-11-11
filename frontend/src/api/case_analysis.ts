export type CaseAnalysis = {
  analysis: {
    Observations: string[];
    OverallAssesment: string[];
  };
  input_tokens: number;
  output_tokens: number;
  stop_reason: string;
};

export async function analyseCase(caseId: string): Promise<CaseAnalysis> {
  const response = await fetch(
    `http://localhost:8000/endpoints/${encodeURIComponent(caseId.trim())}`
  );

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`No case found with ID “${caseId.trim()}”.`);
    }
    const detail = await response.json().catch(() => null);
    throw new Error(
      detail?.detail ?? `Case analysis failed (${response.status}).`
    );
  }

  return response.json();
}
