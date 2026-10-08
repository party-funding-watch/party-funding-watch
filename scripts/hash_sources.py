"""
Fingerprint and verify archived source PDFs
-------------------------------------------
Why: a SHA-256 hash is a unique fingerprint of a file. Publishing the hash
lets anyone, on any mirror, prove that an archived PDF is byte-for-byte the
same file that was originally downloaded. If someone alters or swaps a
source document, its hash will no longer match.

Usage (from the repository root):
    python scripts/hash_sources.py            # record hashes for new PDFs
    python scripts/hash_sources.py --verify   # check every PDF against its hash

Recording never overwrites an existing hash. If a PDF's content changes,
--verify flags it instead of silently accepting the new version.
"""

import argparse
import csv
import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw_pdfs"
SOURCES_CSV = REPO_ROOT / "data" / "SOURCES.csv"
FIELDS = ["filename", "fy", "publisher", "source_page_url", "pdf_url",
          "downloaded_on", "sha256", "bytes"]


def sha256_of(path: Path) -> str:
    """Hash a file in 1 MB chunks so large PDFs don't fill memory."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rows() -> dict:
    if not SOURCES_CSV.exists():
        return {}
    with SOURCES_CSV.open(newline="", encoding="utf-8") as f:
        return {r["filename"]: r for r in csv.DictReader(f)}


def save_rows(rows: dict) -> None:
    with SOURCES_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for name in sorted(rows):
            w.writerow({k: rows[name].get(k, "") for k in FIELDS})


def record() -> None:
    """Add hashes for PDFs that don't have one yet."""
    rows = load_rows()
    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs in {RAW_DIR.relative_to(REPO_ROOT)}\n")
    added = 0
    for pdf in pdfs:
        row = rows.setdefault(pdf.name, {"filename": pdf.name})
        if row.get("sha256"):
            print(f"   kept     {pdf.name} (already fingerprinted)")
            continue
        row["sha256"] = sha256_of(pdf)
        row["bytes"] = str(pdf.stat().st_size)
        added += 1
        print(f"   recorded {pdf.name}  {row['sha256'][:16]}...")
        # Flag files added by hand, which have no provenance yet
        if not row.get("source_page_url"):
            print("            WARNING: no source URL recorded. Fill it in SOURCES.csv by hand.")
    save_rows(rows)
    print(f"\nVERDICT: {added} new fingerprint(s) recorded. Commit data/SOURCES.csv with the PDFs.")


def verify() -> int:
    """Compare every PDF against its recorded hash. Returns an exit code."""
    rows = load_rows()
    on_disk = {p.name for p in RAW_DIR.glob("*.pdf")}
    ok, problems = 0, []

    for name, row in sorted(rows.items()):
        path = RAW_DIR / name
        if name not in on_disk:
            problems.append(f"MISSING   {name} is listed in SOURCES.csv but not on disk")
        elif not row.get("sha256"):
            problems.append(f"UNHASHED  {name} has no recorded hash (run without --verify)")
        elif sha256_of(path) != row["sha256"]:
            problems.append(f"CHANGED   {name} does not match its recorded hash")
        else:
            ok += 1
    for name in sorted(on_disk - rows.keys()):
        problems.append(f"UNLISTED  {name} is on disk but not in SOURCES.csv")

    print(f"Checked {len(rows)} listed source(s): {ok} verified.\n")
    for p in problems:
        print("   " + p)
    if problems:
        print("\nVERDICT: FAIL. Do not publish until every source verifies.")
        return 1
    print("VERDICT: PASS. Every archived source is intact and matches its fingerprint.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--verify", action="store_true", help="check instead of record")
    args = parser.parse_args()
    if args.verify:
        sys.exit(verify())
    record()
