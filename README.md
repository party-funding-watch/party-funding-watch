# Party Funding Watch

An open, reproducible dashboard of how Indian political parties are funded, built entirely from public filings and published audit analyses.

Every number on the dashboard links back to the original source document, and every source document is archived in this repository with a verifiable SHA-256 hash.

## Why this exists

Political parties in India are not required to disclose donors who give less than Rs 20,000. The Association for Democratic Reforms (ADR) analyses party filings with the Election Commission of India (ECI) every year and reports how much income comes from known and unknown sources. This project turns those yearly reports into one consistent, comparable time series that anyone can explore, verify, and reuse.

## Principles

1. **Traceable:** every figure cites its source PDF, page, and table.
2. **Neutral:** all parties are covered with the same method. The dashboard reports what filings show; it does not allege wrongdoing.
3. **Reproducible:** one command rebuilds the full dataset from the archived PDFs.
4. **Durable:** code, data, and site are mirrored across multiple hosts and archives (see `MIRRORS.md`).
5. **Correctable:** errors are fixed publicly (see `CORRECTIONS.md`).

## Repository layout

```
data/
  raw_pdfs/        Archived source PDFs, never edited
  processed/       Clean CSVs produced by the pipeline
  SOURCES.csv      Source URL, download date, and SHA-256 for every PDF
pipeline/          Scripts that turn PDFs into the dataset, run in numbered order
scripts/           Maintenance utilities (hashing, verification)
site/              Static dashboard (added in a later batch)
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
# --prefer-binary installs ready-made packages instead of compiling from source.
# Needed on Intel Macs without Xcode tools (the newest `cryptography` has no
# prebuilt version there); harmless everywhere else.
pip install --prefer-binary -r requirements.txt

python pipeline/01_fetch_and_inventory.py   # download reports, list their tables
python scripts/hash_sources.py              # record SHA-256 of every PDF
python scripts/hash_sources.py --verify     # confirm no PDF has changed
```

## Methodology note: the FY 2023-24 break

Until FY 2022-23, ADR counted electoral bond income as "unknown sources." From FY 2023-24 onward, after the Supreme Court judgment made bond data public, ADR counts it as known. This dataset therefore stores electoral bonds as a separate column every year, so both "unknown including bonds" and "unknown excluding bonds" can be compared consistently across time.

## Licences

- **Code:** GNU AGPL-3.0 (see `LICENSE`)
- **Processed data:** Creative Commons Attribution 4.0 (see `DATA_LICENSE.md`)
- **Source documents:** remain the work of their publishers (ADR, ECI). They are archived here for verification, with attribution.

## Data sources

- Association for Democratic Reforms, Political Party Watch: https://adrindia.org/research-and-report/political-party-watch
- Election Commission of India, party contribution reports and audited accounts: https://www.eci.gov.in

## Contributing

See `CONTRIBUTING.md`. Corrections and new data years are especially welcome.
