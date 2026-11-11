"""Run cleaning and corpus generation in one command."""

from __future__ import annotations

from pathlib import Path

from build_corpus import build_corpus
from data_cleaning import process_corpus


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data_dir = ROOT / "Data"
    process_corpus(
        source_dir=data_dir / "Original_data",
        metadata_path=ROOT / "lynceus_answer_key_file_map.csv",
        cleaned_dir=data_dir / "Cleaned_data",
        manifest_path=data_dir / "manifest.csv",
        quality_report_path=data_dir / "quality_report.csv",
    )
    build_corpus(
        cleaned_dir=data_dir / "Cleaned_data",
        manifest_path=data_dir / "manifest.csv",
        output_path=data_dir / "corpus.py",
    )


if __name__ == "__main__":
    main()
