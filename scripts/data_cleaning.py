"""Clean the Lynceus case corpus and create traceable quality reports."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import unicodedata
from pathlib import Path


MAP_COLUMNS = ("File", "Deck no.", "Delivery", "Round", "Version given")


def normalize_text(text: str) -> str:
    """Normalize whitespace and Unicode without changing the source language."""
    # Keep the words and punctuation intact; this step only removes formatting noise.
    text = text.replace("\ufeff", "")
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(character for character in text if character in "\n\t" or ord(character) >= 32)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_metadata(metadata_path: Path) -> dict[str, dict[str, str]]:
    with metadata_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or any(column not in reader.fieldnames for column in MAP_COLUMNS):
            raise ValueError(f"Metadata must contain columns: {', '.join(MAP_COLUMNS)}")
        return {row["File"]: row for row in reader if row.get("File")}


def quality_status(text: str, metadata: dict[str, str] | None) -> tuple[str, str]:
    warnings: list[str] = []
    if metadata is None:
        warnings.append("missing_metadata")
    if not text.strip():
        warnings.append("empty_text")
    elif len(text.split()) < 20:
        warnings.append("short_text")
    if warnings:
        return "warn", ";".join(warnings)
    return "pass", ""


def process_corpus(
    source_dir: Path,
    metadata_path: Path,
    cleaned_dir: Path,
    manifest_path: Path,
    quality_report_path: Path,
) -> None:
    metadata = read_metadata(metadata_path)
    source_files = sorted(source_dir.glob("*.txt"))
    source_names = {path.name for path in source_files}
    rows: list[dict[str, str]] = []

    # The cleaned folder is separate so the original files remain untouched.
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    for source_path in source_files:
        original_text = source_path.read_text(encoding="utf-8-sig")
        cleaned_text = normalize_text(original_text)
        status, warnings = quality_status(cleaned_text, metadata.get(source_path.name))
        output_path = cleaned_dir / source_path.name

        if cleaned_text.strip():
            output_path.write_text(cleaned_text, encoding="utf-8", newline="\n")

        metadata_row = metadata.get(source_path.name, {})
        rows.append(
            {
                "case_id": source_path.stem,
                "file_name": source_path.name,
                "source_file": str(source_path),
                "cleaned_file": str(output_path) if cleaned_text.strip() else "",
                "delivery": metadata_row.get("Delivery", ""),
                "round": metadata_row.get("Round", ""),
                "version_given": metadata_row.get("Version given", ""),
                "character_count": str(len(cleaned_text.strip())),
                "word_count": str(len(cleaned_text.split())),
                "sha256": sha256_text(cleaned_text),
                "quality_status": status,
                "quality_warnings": warnings,
            }
        )

    # Keep missing files in the manifest so the team can see the full expected set.
    for file_name, metadata_row in sorted(metadata.items()):
        if file_name not in source_names:
            rows.append(
                {
                    "case_id": Path(file_name).stem,
                    "file_name": file_name,
                    "source_file": "",
                    "cleaned_file": "",
                    "delivery": metadata_row.get("Delivery", ""),
                    "round": metadata_row.get("Round", ""),
                    "version_given": metadata_row.get("Version given", ""),
                    "character_count": "",
                    "word_count": "",
                    "sha256": "",
                    "quality_status": "missing_source",
                    "quality_warnings": "source_file_not_found",
                }
            )

    manifest_columns = list(rows[0].keys()) if rows else []
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=manifest_columns)
        writer.writeheader()
        writer.writerows(rows)

    quality_rows = [
        {
            "case_id": row["case_id"],
            "file_name": row["file_name"],
            "quality_status": row["quality_status"],
            "quality_warnings": row["quality_warnings"],
        }
        for row in rows
        if row["quality_status"] != "pass"
    ]
    with quality_report_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["case_id", "file_name", "quality_status", "quality_warnings"],
        )
        writer.writeheader()
        writer.writerows(quality_rows)

    print(f"Processed source files: {len(source_files)}")
    print(f"Metadata rows: {len(metadata)}")
    print(f"Missing source files: {sum(row['quality_status'] == 'missing_source' for row in rows)}")
    print(f"Cleaned files: {sum(bool(row['cleaned_file']) for row in rows)}")
    print(f"Manifest: {manifest_path}")
    print(f"Quality report: {quality_report_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("Data") / "Original_data")
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--cleaned-dir", type=Path, default=Path("Data") / "Cleaned_data")
    parser.add_argument("--manifest", type=Path, default=Path("Data") / "manifest.csv")
    parser.add_argument(
        "--quality-report",
        type=Path,
        default=Path("Data") / "quality_report.csv",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    process_corpus(
        source_dir=arguments.source_dir,
        metadata_path=arguments.metadata,
        cleaned_dir=arguments.cleaned_dir,
        manifest_path=arguments.manifest,
        quality_report_path=arguments.quality_report,
    )
