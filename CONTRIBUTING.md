# Contributing

Thank you for helping keep political funding data open and verifiable.

## Ground rules

1. **Every number needs a source.** A data change must cite the source PDF,
   page number, and table. Pull requests without a source are not merged.
2. **Same method for every party.** No party is singled out or excluded.
3. **Describe, don't accuse.** Use the terms the filings use ("unknown
   sources", "electoral bonds"). Interpretation belongs in clearly labelled
   methodology notes, not in data labels.
4. **Never edit raw PDFs.** Files in `data/raw_pdfs/` are archived originals.
   If a publisher issues a revised report, add it as a new file and record
   it in `data/SOURCES.csv`.

## Adding a new financial year

1. Add the ADR report landing page to `REPORT_PAGES` in
   `pipeline/01_fetch_and_inventory.py`.
2. Run the pipeline and `python scripts/hash_sources.py`.
3. Commit the new PDF, the updated `data/SOURCES.csv`, and the processed rows.
4. Open a pull request describing what changed.

## Reporting an error

Open an issue with the label `correction`, linking the source document and
the value you believe is wrong. Confirmed corrections are logged in
`CORRECTIONS.md`.

## Maintainers

At least two maintainers must hold admin rights on the organisation and on
every mirror, so the project never depends on one person.
