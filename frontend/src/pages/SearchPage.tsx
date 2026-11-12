import { useState, type FormEvent } from "react";
import {
  reloadSearchIndex,
  searchCases,
  type SearchResult,
} from "../api/real_search";

function isDuplicateText(first: string, second: string): boolean {
  const normalize = (value: string) => value.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
  const a = normalize(first);
  const b = normalize(second);
  return Boolean(a && b && (a === b || (Math.min(a.length, b.length) > 60 && (a.includes(b) || b.includes(a)))));
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [searchMethod, setSearchMethod] = useState("");
  const [indexLoading, setIndexLoading] = useState(false);
  const [indexMessage, setIndexMessage] = useState("");

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runSearch(query);
  }

  async function runSearch(searchQuery: string) {
    if (!searchQuery.trim() || loading) return;

    setLoading(true);
    setError("");
    setMessage("");
    setResults([]);
    setHasSearched(false);

    try {
      const response = await searchCases(searchQuery.trim());

      setResults(response.results);
      setMessage(response.message ?? "");
      setSearchMethod(response.embedder);
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

  async function handleReloadIndex() {
    setIndexLoading(true);
    setIndexMessage("");
    setError("");
    try {
      const response = await reloadSearchIndex();
      setSearchMethod(response.embedder);
      const sourceOnly = response.cases - response.enriched;
      setIndexMessage(`Index updated: ${response.cases} source cases, ${response.enriched} structured records, ${sourceOnly} cases using source text only. Run the search again to use the refreshed index.`);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not reload case records.");
    } finally {
      setIndexLoading(false);
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

        <button className="reload-index-button" type="button" disabled={indexLoading} onClick={handleReloadIndex}>
          {indexLoading ? "Reloading records…" : "Reload cases and structured records"}
        </button>
      </form>

      {indexMessage && <p className="notice" role="status">{indexMessage}</p>}

      <div role="status" aria-live="polite">
        {loading && <p>Finding relevant projects...</p>}

        {hasSearched && (message || results.length === 0) && (
          <p className="notice">
            {message || "No matching cases found."}
          </p>
        )}

        {hasSearched && results.length > 0 && (
          <p>
            {results.length} matching{" "}
            {results.length === 1 ? "project" : "projects"}
          {searchMethod && ` · ${searchMethod}`}
          </p>
        )}

      {hasSearched && searchMethod === "none" && (
        <p className="notice">Semantic embeddings are not configured. Search is using keyword matching only, so cross-vocabulary matches may be missed.</p>
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
              Match {index + 1} · {result.case_id} · {result.strong_match ? "Strong match" : "Weak match"}
            </p>

            <h2>{result.case_id}</h2>

            <p className="hint">
              {result.enriched
                ? `${[result.sector, result.country, result.language].filter(Boolean).join(" · ") || "Structured record loaded"} · ${result.reviewed_by_human ? "human reviewed" : "not human reviewed"}`
                : "Source text only · no structured record loaded"}
            </p>

            <div className="match-reason">
              <h3>Why this case was chosen</h3>
              <p>{result.why || "No match explanation available."}</p>
            </div>

            {result.summary && (
              <>
                <h3>{result.enriched ? "Structured case summary" : "Case text preview"}</h3>
                <p>{result.summary}</p>
              </>
            )}

            {result.problem_plain && !isDuplicateText(result.summary, result.problem_plain) && (
              <>
                <h3>Client problem</h3>
                <p>{result.problem_plain}</p>
              </>
            )}

            <details>
              <summary>How it matched and details about the work</summary>
              <h3>Meaning match</h3>
              <p className="field-help">Shows how closely this case’s meaning matches your question. “Keyword only” means no semantic similarity score was available.</p>
              <p>{result.similarity ?? "Keyword only"}</p>
              <h3>Search ranking score</h3>
              <p className="field-help">An internal value the search uses to order results. It is not a percentage or a certainty rating.</p>
              <p>{result.score}</p>
              {result.enriched ? <>
                <h3>Capability</h3>
                <p className="field-help">What the team did for the client, including the approach, services or technology used.</p>
                <p>{result.capability || "No capability details are in this record."}</p>
                <h3>Scale and outcomes</h3>
                <p className="field-help">The reported size of the work and its results, such as systems involved, time saved or costs reduced.</p>
                <p>{result.scale_outcomes || "No scale or outcome details are in this record."}</p>
                <h3>Reusable approach</h3>
                <p className="field-help">An approach from this case that may be useful for another client’s problem.</p>
                <p>{result.reusable || "No reusable approach is described in this record."}</p>
              </> : <p>No structured enrichment record is loaded for this case. Search is using the original case text.</p>}
            </details>

            <p className="hint source-path">
              Source: {result.source_file || result.source_path}
            </p>
          </article>
        ))}
      </section>
    </main>
  );
}
