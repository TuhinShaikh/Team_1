import { useEffect, useState } from "react";
import {
  getDocuments,
  type CaseDocument,
} from "../api/documents";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<CaseDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadCount, setReloadCount] = useState(0);

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