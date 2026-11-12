import { useEffect, useState, type FormEvent } from "react";
import {
  getDocuments,
  type CaseDocument,
} from "../api/documents";
import { analyseCase, type CaseAnalysis } from "../api/case_analysis";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<CaseDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadCount, setReloadCount] = useState(0);
  const [caseId, setCaseId] = useState("");
  const [caseAnalysis, setCaseAnalysis] = useState<CaseAnalysis | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState("");
  const [analysedCaseId, setAnalysedCaseId] = useState("");

  async function handleCaseAnalysis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!caseId.trim() || analysisLoading) return;

    setAnalysisLoading(true);
    setAnalysisError("");
    setCaseAnalysis(null);
    setAnalysedCaseId("");
    try {
      const response = await analyseCase(caseId);
      setCaseAnalysis(response);
      setAnalysedCaseId(caseId.trim());
    } catch (error) {
      setAnalysisError(
        error instanceof Error ? error.message : "Could not analyse this case."
      );
    } finally {
      setAnalysisLoading(false);
    }
  }

  useEffect(() => {
    const controller = new AbortController();

    async function loadDocuments() {
      setLoading(true);
      setError("");

      try {
        const data = await getDocuments(controller.signal);

        if (!controller.signal.aborted) {
          setDocuments(data);
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setError(
            error instanceof Error
              ? error.message
              : "Could not load documents."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadDocuments();

    return () => controller.abort();
  }, [reloadCount]);

  return (
    <main className="app">
      <header>
        <p className="eyebrow">PROJECT LIBRARY</p>

        <h1>All documents</h1>

        <p className="intro">
          Browse the original case studies in the corpus.
        </p>

        <button
          type="button"
          disabled={loading}
          onClick={() => setReloadCount((count) => count + 1)}
        >
          {loading ? "Loading..." : "Reload documents"}
        </button>
      </header>

      <section className="search-panel case-lookup" aria-labelledby="case-lookup-title">
        <h2 id="case-lookup-title">Find a case by ID</h2>
        <p className="hint">Enter a case ID to view its observations and overall assessment. AI analysis uses the configured model; saved case records are used as a fallback.</p>
        <form onSubmit={handleCaseAnalysis}>
          <label htmlFor="case-id">Case ID</label>
          <input
            id="case-id"
            type="text"
            placeholder="For example: case-209"
            value={caseId}
            onChange={(event) => setCaseId(event.target.value)}
            disabled={analysisLoading}
            required
          />
          <button type="submit" disabled={analysisLoading || !caseId.trim()}>
            {analysisLoading ? "Analysing..." : "Analyse case"}
          </button>
        </form>
        {analysisLoading && <p role="status">Preparing case analysis...</p>}
        {analysisError && <p className="error" role="alert">{analysisError}</p>}
        {caseAnalysis && (
          <article className="case-analysis" aria-live="polite">
            <p className="case-id">Analysis for {analysedCaseId}</p>
            {caseAnalysis.analysis_source === "saved_enrichment" && (
              <p className="notice">
                Showing the saved structured record{caseAnalysis.reviewed_by_human ? " (human reviewed)." : " (not marked as human reviewed)."}
              </p>
            )}
            {caseAnalysis.analysis_source === "source_text" && (
              <p className="notice">Showing source sentences only. Configure ANTHROPIC_API_KEY to generate an AI assessment.</p>
            )}
            {caseAnalysis.analysis_source === "anthropic" && <p className="hint">AI-generated analysis. Check it against the source text.</p>}
            <h3>Observations</h3>
            <ul>{caseAnalysis.analysis.Observations.map((item, index) => <li key={index}>{item}</li>)}</ul>
            <h3>Overall assessment</h3>
            <ul>{caseAnalysis.analysis.OverallAssesment.map((item, index) => <li key={index}>{item}</li>)}</ul>
          </article>
        )}
      </section>

      <div role="status" aria-live="polite">
        {loading && <p>Loading documents...</p>}

        {!loading && !error && (
          <p>
            {documents.length}{" "}
            {documents.length === 1 ? "document" : "documents"} loaded
          </p>
        )}
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && documents.length === 0 && (
        <p className="notice">No documents available.</p>
      )}

      {!loading && !error && (
        <section className="results" aria-label="All documents">
          {documents.map((document) => (
            <article
              className="result-card"
              id={document.case_id}
              key={document.case_id}
            >
              <p className="case-id">{document.case_id}</p>

              <h2>{document.delivery}</h2>

              <p className="hint">
                Language / version: {document.language}
              </p>

              <p className="document-body">
                {document.body}
              </p>

              <p className="hint source-path">
                Source: {document.source_file}
              </p>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
