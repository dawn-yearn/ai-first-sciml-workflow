"""Inspect local PDFs. Structural checks do not verify paper identity."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def inspect_pdf(path):
    from pypdf import PdfReader

    path = Path(path)
    with path.open("rb") as stream:
        header = stream.read(1024)
        if b"%PDF-" not in header:
            raise ValueError("PDF header not found; this may be HTML or an error response")
        stream.seek(0)
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF: inspect access and readability manually")
    pages = len(reader.pages)
    if pages == 0:
        raise ValueError("PDF has no pages")
    first_page = " ".join((reader.pages[0].extract_text() or "").split())
    return {
        "file": path.name,
        "status": "readable_pdf",
        "bytes": path.stat().st_size,
        "sha256": digest,
        "pages": pages,
        "first_page_text": first_page[:1400],
        "identity_verified": False,
        "next_check": "Compare title, authors, DOI and version with the expected paper",
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, help="Optional new JSON file; existing files are not replaced")
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("Output already exists; choose a new filename")
    results = []
    failed = False
    for path in args.pdfs:
        try:
            results.append(inspect_pdf(path))
        except Exception as exc:
            failed = True
            results.append({"file": path.name, "status": "failed", "error": str(exc)})
    payload = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(payload + "\n")
    print(payload)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
