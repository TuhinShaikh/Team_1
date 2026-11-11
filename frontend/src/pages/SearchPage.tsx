import { useState, type FormEvent } from "react";
import {
  searchCases,
  type SearchResult,
} from "../api/real_search";
import { analyseCase, type CaseAnalysis } from "../api/case_analysis";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [caseId, setCaseId] = useState("");
  const [caseAnalysis, setCaseAnalysis] = useState<CaseAnalysis | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState("");
  const [analysedCaseId, setAnalysedCaseId] = useState("");

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!query.trim() || loading) return;

    setLoading(true);
    setError("");
    setMessage("");
    setResults([]);
    setHasSearched(false);

    try {
      const response = await searchCases(query.trim());

      setResults(response.results);
      setMessage(response.message ?? "");
      setHasSearched(true);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

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

  return (
    <main className="app">
      <header>
        <p className="eyebrow"><span className="eyebrow-dot" /> PAST WORK. NEW POSSIBILITIES.</p>
        <h1>Find the work<br /><span>that moves you forward.</span></h1>

        <p className="intro">
          Describe your client’s challenge. Discover proven experience, ideas and outcomes from across the project library.
        </p>
      </header>

      <form className="search-panel" onSubmit={handleSearch}>
        <label htmlFor="search-query">
          What does your client need?
        </label>

        <textarea
          id="search-query"
          rows={4}
          placeholder="For example: A client wants to improve customer support using AI."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          disabled={loading}
          required
        />

        <button
          type="submit"
          disabled={loading || !query.trim()}
        >
          {loading ? "Searching..." : "Find projects"}
        </button>
      </form>

      <section className="search-panel case-lookup" aria-labelledby="case-lookup-title">
        <h2 id="case-lookup-title">Search individual case</h2>
        <p className="hint">Enter a case ID to get an AI-generated analysis of that case.</p>
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
            <h3>Observations</h3>
            <ul>{caseAnalysis.analysis.Observations.map((item, index) => <li key={index}>{item}</li>)}</ul>
            <h3>Overall assessment</h3>
            <ul>{caseAnalysis.analysis.OverallAssesment.map((item, index) => <li key={index}>{item}</li>)}</ul>
          </article>
        )}
      </section>

      <div role="status" aria-live="polite">
        {loading && <p>Finding relevant projects...</p>}

        {hasSearched && results.length === 0 && (
          <p className="notice">
            {message || "No strong match found."}
          </p>
        )}

        {hasSearched && results.length > 0 && (
          <p>
            {results.length} matching{" "}
            {results.length === 1 ? "project" : "projects"}
          </p>
        )}
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {!loading && !hasSearched && !error && (
        <p className="hint">
          Enter a client problem to get started.
        </p>
      )}

      <section
        className="results"
        aria-label="Search results"
        aria-busy={loading}
      >
        {results.map((result, index) => (
          <article
            className="result-card"
            key={result.case_id}
          >
            <p className="case-id">
              Match {index + 1} · {result.case_id}
            </p>

            <h2>{result.summary || result.case_id}</h2>

            <p className="hint">
              {result.language || "Language not provided"}
            </p>

            <div className="match-reason">
              <h3>Case overview</h3>
              <p>{result.body}</p>
            </div>

            <p className="hint source-path">
              Source: {result.source_path}
            </p>
          </article>
        ))}
      </section>
    </main>
  );
}
