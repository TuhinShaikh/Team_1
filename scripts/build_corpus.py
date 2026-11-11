"""Build a Python corpus list from the cleaned files and manifest."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def build_corpus(cleaned_dir: Path, manifest_path: Path, output_path: Path) -> int:
    """Write available cleaned cases as a Python CORPUS list."""
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    documents: list[dict[str, str]] = []
    for row in rows:
        cleaned_file = row.get("cleaned_file", "")
        if not cleaned_file:
            continue

        file_path = Path(cleaned_file)
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
        if not file_path.exists():
            file_path = cleaned_dir / Path(cleaned_file).name
        if not file_path.exists():
            raise FileNotFoundError(f"Cleaned file listed in manifest was not found: {file_path}")

        documents.append(
            {
                "document": row["case_id"],
                "case_id": row["case_id"],
                "language": row.get("version_given", ""),
                "body": file_path.read_text(encoding="utf-8").strip(),
                "source_file": row["cleaned_file"],
                "delivery": row.get("delivery", ""),
                "round": row.get("round", ""),
            }
        )

    output = (
        '"""Generated corpus for search and evaluation. Do not edit by hand."""\n\n'
        "from typing import Any\n\n\n"
        "CORPUS: list[dict[str, Any]] = "
        + json.dumps(documents, ensure_ascii=False, indent=4)
        + "\n"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8", newline="\n")
    print(f"Generated {len(documents)} corpus documents: {output_path}")
    return len(documents)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cleaned-dir", type=Path, default=Path("Data") / "Cleaned_data")
    parser.add_argument("--manifest", type=Path, default=Path("Data") / "manifest.csv")
    parser.add_argument("--output", type=Path, default=Path("Data") / "corpus.py")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build_corpus(arguments.cleaned_dir, arguments.manifest, arguments.output)
