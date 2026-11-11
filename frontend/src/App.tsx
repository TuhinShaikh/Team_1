import { useState } from "react";
import SearchPage from "./pages/SearchPage";
import DocumentsPage from "./pages/DocumentsPage";

export default function App() {
  const [page, setPage] = useState<"search" | "documents">(
    "search"
  );
  const [accessibilityOpen, setAccessibilityOpen] = useState(false);
  const [largeText, setLargeText] = useState(false);
  const [highContrast, setHighContrast] = useState(false);

  return (
    <div className={`${largeText ? "large-text " : ""}${highContrast ? "high-contrast" : ""}`}>
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

          <button
            type="button"
            className="accessibility-button"
            aria-expanded={accessibilityOpen}
            aria-controls="accessibility-controls"
            onClick={() => setAccessibilityOpen((open) => !open)}
          >
            <span aria-hidden="true">◐</span> Accessibility
          </button>
        </div>
      </nav>

      {accessibilityOpen && (
        <section className="accessibility-panel" id="accessibility-controls" aria-label="Accessibility settings">
          <div>
            <strong>Accessibility settings</strong>
            <p>Adjust the display to make Lynceus easier to read.</p>
          </div>
          <button type="button" className={largeText ? "setting-active" : "setting-button"} aria-pressed={largeText} onClick={() => setLargeText((enabled) => !enabled)}>
            Larger text {largeText ? "· On" : "· Off"}
          </button>
          <button type="button" className={highContrast ? "setting-active" : "setting-button"} aria-pressed={highContrast} onClick={() => setHighContrast((enabled) => !enabled)}>
            High contrast {highContrast ? "· On" : "· Off"}
          </button>
        </section>
      )}

      {page === "search" ? (
        <SearchPage />
      ) : (
        <DocumentsPage />
      )}
    </div>
  );
}
