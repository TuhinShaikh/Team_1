import { useState } from "react";
import SearchPage from "./pages/SearchPage";
import DocumentsPage from "./pages/DocumentsPage";

export default function App() {
  const [page, setPage] = useState<"search" | "documents">(
    "search"
  );

  return (
    <>
      <nav className="navbar" aria-label="Main navigation">
        <div className="navbar-inner">
          <button
            type="button"
            className="navbar-brand"
            onClick={() => setPage("search")}
            aria-label="Lynceus home"
          >
            Lynceus
            
          </button>

          <div className="navbar-links">
            <button
              type="button"
              className={`nav-button ${
                page === "search" ? "active" : ""
              }`}
              aria-pressed={page === "search"}
              onClick={() => setPage("search")}
            >
              Search projects
            </button>

            <button
              type="button"
              className={`nav-button ${
                page === "documents" ? "active" : ""
              }`}
              aria-pressed={page === "documents"}
              onClick={() => setPage("documents")}
            >
              All documents
            </button>
          </div>
        </div>
      </nav>

      {page === "search" ? (
        <SearchPage />
      ) : (
        <DocumentsPage />
      )}
    </>
  );
}
