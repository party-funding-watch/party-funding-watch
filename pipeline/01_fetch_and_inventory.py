"""
Pipeline step 01: fetch ADR reports and inventory their tables
---------------------------------------------------------------
What this does:
  1. Visits each ADR report landing page and finds the English PDF link.
  2. Downloads the PDF into data/raw_pdfs/ (skips files already archived).
  3. Records provenance (source page, PDF URL, download date) in
     data/SOURCES.csv, so every number can later be traced to its origin.
  4. Lists every table inside each PDF and flags the ones that look like
     income-breakdown tables, to guide the extraction step (02).

Why provenance matters: if a source page is later taken down, SOURCES.csv
plus the archived PDF still prove where each figure came from.

Run from the repository root:
    python pipeline/01_fetch_and_inventory.py
"""

import csv
import datetime as dt
import re
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import pdfplumber
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Paths: resolved from this file's location, so the script works no matter
# which folder VS Code's terminal happens to be in.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw_pdfs"
SOURCES_CSV = REPO_ROOT / "data" / "SOURCES.csv"
INVENTORY_CSV = REPO_ROOT / "adr_table_inventory.csv"  # scratch, git-ignored
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Report registry: one ADR landing page per financial year.
# We scrape the PDF link from each page instead of hard-coding it, because
# ADR sometimes renames files. Add older years from:
#   https://adrindia.org/research-and-report/political-party-watch
# ---------------------------------------------------------------------------
REPORT_PAGES = {
    "2023-24": "https://www.adrindia.org/content/analysis-of-sources-of-funding-of-national-parties-fy-2023-24",
    "2022-23": "https://adrindia.org/content/analysis-sources-funding-national-parties-fy-2022-23",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (party-funding-watch, open public-interest data project)"}
SOURCE_FIELDS = ["filename", "fy", "publisher", "source_page_url", "pdf_url",
                 "downloaded_on", "sha256", "bytes"]


def find_english_pdf(page_url: str) -> str | None:
    """Return the English report PDF link from an ADR landing page."""
    html = requests.get(page_url, headers=HEADERS, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    # ADR often writes links as site-relative paths ("/sites/default/files/...").
    # urljoin turns them into full addresses using the landing page's domain,
    # and leaves links that are already absolute unchanged.
    pdf_links = [urljoin(page_url, a["href"]) for a in soup.find_all("a", href=True)
                 if a["href"].lower().endswith(".pdf")]
    # Prefer the English version; fall back to the first PDF on the page
    english = [link for link in pdf_links if "english" in link.lower()]
    return (english or pdf_links or [None])[0]


def load_sources() -> dict:
    """Read existing provenance rows, keyed by filename."""
    if not SOURCES_CSV.exists():
        return {}
    with SOURCES_CSV.open(newline="", encoding="utf-8") as f:
        return {row["filename"]: row for row in csv.DictReader(f)}


def save_sources(rows: dict) -> None:
    """Write provenance rows back, sorted for stable git diffs."""
    with SOURCES_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SOURCE_FIELDS)
        writer.writeheader()
        for name in sorted(rows):
            writer.writerow({k: rows[name].get(k, "") for k in SOURCE_FIELDS})


# ---------------------------------------------------------------------------
# STEP 1: download and record provenance
# ---------------------------------------------------------------------------
print("STEP 1: locating and downloading ADR reports\n")
sources = load_sources()
pdf_paths = {}

for fy, page in REPORT_PAGES.items():
    print(f"FY {fy}")
    dest = RAW_DIR / f"adr_sources_of_funding_national_FY{fy}.pdf"

    # Archived PDFs are never re-downloaded: the archive is the source of truth
    if dest.exists():
        print(f"   already archived: {dest.name}")
        pdf_paths[fy] = dest
        continue

    try:
        pdf_url = find_english_pdf(page)
    except requests.RequestException as e:
        print(f"   WARNING: could not open landing page ({e}). Skipping.")
        continue
    if not pdf_url:
        print("   WARNING: no PDF link found on page. Check the URL manually.")
        continue

    # A failed download for one year should not stop the other years, so we
    # warn and move on, the same way a failed landing page is handled above.
    # Nothing is written to disk unless the download fully succeeded.
    try:
        resp = requests.get(pdf_url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"   WARNING: could not download {pdf_url} ({e}). Skipping.")
        continue
    dest.write_bytes(resp.content)
    print(f"   saved {dest.name} ({len(resp.content) / 1024:.0f} KB)")

    # sha256 and bytes are filled in by scripts/hash_sources.py
    sources[dest.name] = {
        "filename": dest.name, "fy": fy, "publisher": "ADR",
        "source_page_url": page, "pdf_url": pdf_url,
        "downloaded_on": dt.date.today().isoformat(),
    }
    pdf_paths[fy] = dest

save_sources(sources)
print(f"\nProvenance recorded in {SOURCES_CSV.relative_to(REPO_ROOT)}")

# ---------------------------------------------------------------------------
# STEP 2: table inventory
# The core table we want splits each party's income into known donors,
# other known, electoral bonds, and unknown. Its header row usually
# contains one of these keywords.
# ---------------------------------------------------------------------------
KEYWORDS = re.compile(r"unknown|total income|electoral bond|known", re.I)

print("\nSTEP 2: table inventory per report\n")
inventory = []
for fy, path in pdf_paths.items():
    with pdfplumber.open(path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            for t_idx, table in enumerate(page.extract_tables()):
                if not table or not table[0]:
                    continue
                header = " | ".join(str(c or "").strip() for c in table[0])
                inventory.append({
                    "fy": fy, "page": page_no, "table_idx": t_idx,
                    "rows": len(table), "cols": len(table[0]),
                    "looks_relevant": bool(KEYWORDS.search(header)),
                    "header": header[:120],
                })

inv = pd.DataFrame(inventory)
if inv.empty:
    print("VERDICT: no tables extracted from any report. The PDFs may be scanned images; step 02 will need OCR.")
else:
    inv.to_csv(INVENTORY_CSV, index=False)
    print(f"Found {len(inv)} tables across {len(pdf_paths)} reports.")
    for fy, grp in inv.groupby("fy"):
        hits = grp[grp["looks_relevant"]]
        print(f"\nFY {fy}: {len(grp)} tables, {len(hits)} look like income-breakdown tables")
        for _, r in hits.iterrows():
            print(f"   page {r.page}, table {r.table_idx} ({r.rows}x{r.cols}): {r.header}")
        if hits.empty:
            print("   VERDICT: no keyword match. Tables may be images; step 02 will need OCR for this year.")

print("\nNEXT: run  python scripts/hash_sources.py  to fingerprint the archived PDFs.")
