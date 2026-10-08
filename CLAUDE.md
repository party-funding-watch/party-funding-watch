# CLAUDE.md: project context for Claude Code

## What this project is
Party Funding Watch: an open-source, takedown-resilient public dashboard of Indian
political party funding, built from ADR (Association for Democratic Reforms)
"Analysis of Sources of Funding of National Parties" reports and ECI filings.
Later phases may add CAG audit data (pending utilisation certificates, AC bills).

## Environment
- macOS, zsh, VS Code. Use `python3` to create the venv; inside `.venv` use `python`/`pip`.
- Activate with `source .venv/bin/activate`.
- Run all scripts from the repo root.

## How I want to work
- Deliver code in **incremental batches**. Finish one batch, let me review and run it,
  then move to the next. Do not build the whole thing end to end in one go.
- Comment code thoroughly, explaining the reasoning, and use print statements generously.
- Scripts must print **plain-language verdicts and interpretation** next to raw numbers
  (e.g. "VERDICT: PASS ..."), never bare tables.
- **Never use em dashes** in any code, comments, docs, or messages.
- Explain any git/GitHub/hosting step plainly; I know data analytics well but am new
  to open-source project setup.

## Non-negotiable project principles
1. Every figure is traceable to a source PDF, page, and table.
2. Neutral language: use filing terms ("unknown sources", "electoral bonds"). The
   dashboard describes, it does not accuse. All parties are treated identically.
3. Fully reproducible: one command rebuilds the dataset from `data/raw_pdfs/`.
4. Never edit or delete files in `data/raw_pdfs/`. Revised reports are added as new files.
5. Every PDF is fingerprinted in `data/SOURCES.csv`; `python scripts/hash_sources.py --verify`
   must PASS before anything is published.
6. Licences: code AGPL-3.0, processed data CC BY 4.0, source PDFs remain the publishers'.

## Data schema (target for data/processed/)
One row per party per financial year:
`fy, party, total_income, known_donors_above_20k, electoral_bonds, other_known,
unknown_excl_eb, coupon_sales, source_pdf, source_page, source_basis`

`source_basis` is the party document ADR compiled the figures from:
`audit_report` or `income_expenditure_statement` (see methodology below).

## Methodology break (critical)
Up to FY 2022-23, ADR counted electoral bonds as "unknown sources". From FY 2023-24
it counts them as known. Always store electoral bonds as a separate column so the
dashboard can show both "unknown incl. bonds" and "unknown excl. bonds" consistently.

A second difference: the underlying party documents. ADR's FY 2023-24 tables are titled
"as per the audit reports of National Parties", while FY 2022-23 tables say "as per the
income-expenditure statements" (page 5 of each report). Record this per row in
`source_basis` (`audit_report` for FY 2023-24, `income_expenditure_statement` for
FY 2022-23) and check the wording for every older year as it is added, rather than
assuming. The dashboard should surface it next to any cross-year comparison.

## Validation targets for FY 2023-24 (from ADR's report page)
- Total income, 6 national parties (BJP, INC, CPI(M), BSP, AAP, NPEP): Rs 5,820.912 cr
- Known donors above Rs 20k: Rs 2,544.278 cr
- Electoral bonds: Rs 2,524.136 cr
- Other known sources: Rs 553.1298 cr
- Unknown sources: Rs 199.3683 cr (3.425%)
  - CPI(M) 82.0759, INC 78.7298, BJP 37.6037, AAP 0.93, NPEP 0.0289 (Rs cr)
- BSP declared no voluntary contributions, coupons, bonds, or unknown income.
FY 2022-23: total Rs 3,076.88 cr; unknown Rs 1,832.88 cr (59.57%), BJP Rs 1,400.23 cr.

## Current status and roadmap
- [x] Batch 0: repo scaffold, licences, governance docs, fetch + inventory script,
      SHA-256 hashing/verify tool.
- [x] Get Batch 0 running locally (venv, pipeline step 01, hashing).
- [ ] Batch 1: GitHub org + first push; GitHub Actions to (a) run `--verify` on every
      push, (b) auto-mirror to Codeberg and GitLab.
- [ ] Batch 2: `pipeline/02_extract.py`, extracting the income-breakdown tables found
      by the inventory into the schema, with checks against the validation targets.
- [ ] Batch 3: add older years (back to FY 2004-05) from ADR Political Party Watch.
- [ ] Batch 4: static dashboard in `site/`, every chart linked to its source.
- [ ] Batch 5: deploy to GitHub Pages + Cloudflare Pages; Zenodo DOI and Wayback
      archiving on each release; fill in `MIRRORS.md`.

Update the checkboxes above as batches are completed.
