#!/usr/bin/env python
"""
ingest_references.py - Reference Document Ingestion

This script ingests reference documents (PDFs, HTML, Markdown) into the
knowledge base for RAG context and grounding.

Usage:
    python scripts/ingest_references.py --source /path/to/document.pdf
    python scripts/ingest_references.py --batch /path/to/references/
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import json
from datetime import datetime


# Supported document types
SUPPORTED_TYPES = {
    ".md": "markdown",
    ".html": "html",
    ".txt": "text",
    ".pdf": "pdf",  # Requires PyPDF2
}

# Metadata schema for ingested references
REFERENCE_SCHEMA = {
    "title": str,
    "source": str,
    "document_type": str,
    "ingested_at": str,
    "checksum": str,
    "size_bytes": int,
    "categories": List[str],
    "tier": int,  # 1-4 evidence hierarchy
}


def compute_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def extract_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from a reference document."""
    checksum = compute_checksum(file_path)
    stats = file_path.stat()

    # Basic metadata
    metadata = {
        "title": file_path.stem,
        "source": str(file_path),
        "document_type": SUPPORTED_TYPES.get(file_path.suffix, "unknown"),
        "ingested_at": datetime.now().isoformat(),
        "checksum": checksum,
        "size_bytes": stats.st_size,
        "categories": ["reference"],
        "tier": 3,  # Default to industry/professional tier
    }

    # Try to extract title from content for markdown/html
    if file_path.suffix in [".md", ".html"]:
        try:
            content = file_path.read_text(encoding="utf-8")
            if file_path.suffix == ".md":
                # Extract first heading
                for line in content.split("\n"):
                    if line.startswith("# "):
                        metadata["title"] = line.lstrip("# ").strip()
                        break
            elif file_path.suffix == ".html":
                # Extract title tag
                import re
                title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
                if title_match:
                    metadata["title"] = title_match.group(1).strip()
        except Exception as e:
            print(f"Warning: Could not extract title from {file_path}: {e}")

    return metadata


def ingest_document(source: Path, references_dir: Path, overwrite: bool = False) -> bool:
    """Ingest a single reference document."""
    if not source.exists():
        print(f"Error: Source file {source} not found")
        return False

    # Determine destination category
    categories = {
        ".pdf": references_dir / "documents",
        ".md": references_dir / "markdown",
        ".html": references_dir / "html",
    }
    dest_dir = categories.get(source.suffix, references_dir / "other")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Extract metadata
    metadata = extract_metadata(source)

    # Check if already exists
    dest_file = dest_dir / f"{metadata['checksum'][:8]}_{source.name}"
    if dest_file.exists() and not overwrite:
        print(f"Skipping {source}: already exists as {dest_file.name}")
        return False

    # Copy file
    import shutil
    shutil.copy2(source, dest_file)

    # Write metadata
    meta_file = dest_file.with_suffix(".meta.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✓ Ingested: {source.name} → {dest_file.name}")
    print(f"  Type: {metadata['document_type']}, Size: {metadata['size_bytes']} bytes")
    print(f"  Checksum: {metadata['checksum'][:16]}...")

    return True


def ingest_batch(source_dir: Path, references_dir: Path, overwrite: bool = False) -> int:
    """Ingest all supported documents from a directory."""
    count = 0
    for file_path in source_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in SUPPORTED_TYPES:
            if ingest_document(file_path, references_dir, overwrite):
                count += 1
    return count


def list_references(references_dir: Path) -> List[Dict[str, Any]]:
    """List all ingested references with metadata."""
    references = []

    for meta_file in references_dir.rglob("*.meta.json"):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                references.append(metadata)
        except Exception as e:
            print(f"Warning: Could not read {meta_file}: {e}")

    return sorted(references, key=lambda r: r["ingested_at"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description="Reference document ingestion")
    parser.add_argument("--source", type=Path, help="Source file or directory to ingest")
    parser.add_argument("--references-dir", type=Path,
                       default=Path(__file__).parent.parent / "references" / "ingested",
                       help="Destination directory for ingested references")
    parser.add_argument("--batch", action="store_true", help="Treat source as directory (batch ingest)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--list", action="store_true", help="List ingested references")
    parser.add_argument("--validate", action="store_true", help="Validate ingested references")

    args = parser.parse_args()

    # Create references directory
    args.references_dir.mkdir(parents=True, exist_ok=True)

    if args.list:
        print("Ingested references:")
        print("-" * 60)
        references = list_references(args.references_dir)
        for ref in references:
            print(f"• {ref['title']}")
            print(f"  Source: {ref['source']}")
            print(f"  Type: {ref['document_type']}, Tier: {ref['tier']}")
            print(f"  Ingested: {ref['ingested_at']}")
            print(f"  Checksum: {ref['checksum'][:16]}...")
            print()

    elif args.validate:
        print("Validating ingested references...")
        references = list_references(args.references_dir)
        valid_count = 0

        for ref in references:
            # Verify checksum
            source_file = Path(ref['source'])
            if not source_file.exists():
                print(f"✗ Missing source: {ref['title']}")
                continue

            current_checksum = compute_checksum(source_file)
            if current_checksum != ref['checksum']:
                print(f"✗ Checksum mismatch: {ref['title']}")
                continue

            valid_count += 1

        print(f"Validated {valid_count}/{len(references)} references")

    elif args.source:
        if args.batch:
            count = ingest_batch(args.source, args.references_dir, args.overwrite)
            print(f"\nIngested {count} documents from {args.source}")
        else:
            ingest_document(args.source, args.references_dir, args.overwrite)

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
