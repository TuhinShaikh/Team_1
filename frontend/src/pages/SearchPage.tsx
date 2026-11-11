import { useState, type FormEvent } from "react";
import {
  searchCases,
  type SearchResult,
} from "../api/search";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

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

  function display(value: string | null | undefined) {
    return value?.trim() || "Not provided";
  }

  return (
    <main className="app">
      <header>
        <p className="eyebrow">PAST WORK. NEW POSSIBILITIES.</p>


        <p className="intro">
          Describe your client's challenge to find relevant past projects.
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

            <h2>{result.case_id}</h2>

            <p className="hint">
              {[
                result.sector,
                result.country,
                result.language,
              ]
                .filter(Boolean)
                .join(" · ") || "No metadata available"}
            </p>

            {result.summary && <p>{result.summary}</p>}

            <div className="match-reason">
              <h3>Client problem</h3>
              <p>{display(result.problem_plain)}</p>
            </div>

            <h3>Technique used</h3>
            <p>{display(result.capability)}</p>

            <h3>Scale and outcomes</h3>
            <p>{display(result.scale_outcomes)}</p>

            <h3>What could be reused</h3>
            <p>{display(result.reusable)}</p>

            <p className="hint source-path">
              Source: {display(result.source_path)}
            </p>
          </article>
        ))}
      </section>
    </main>
  );
}