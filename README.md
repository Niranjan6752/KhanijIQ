# KhanijIQ: prototype

Patent and R&D intelligence for critical minerals (CMiH 2026, Problem Statement 02).

## Run the demo (offline, synthetic data)
```bash
pip install -r requirements.txt
python scripts/make_sample_data.py     # creates data/records.csv (SYNTHETIC demo records)
streamlit run app.py
```
Sample records are synthetic and labelled as such in the app. Never present them as real findings.

## Use real data
1. **Papers:** `python scripts/ingest_openalex.py you@example.com` (Indian-affiliated works, OpenAlex API).
2. **Patents:** export Indian records from Lens.org or Google Patents (BigQuery public dataset), then
   `python scripts/ingest_patents.py export.csv`. Adjust `CANDIDATES` in that script if column names differ.
   Use InPASS only within its terms of use (it has CAPTCHAs), e.g. to verify a sample.
3. **Projects:** add curated rows to `data/projects.csv` (ministry, NMET, CSIR, IIT, PSU pages). Columns match `records.csv`.
4. `python scripts/build_dataset.py` merges everything, normalises organisation names, removes duplicates.
5. Restart or refresh the app.

## Map to the problem statement
| Requirement | Where |
|---|---|
| Search by keyword, mineral, process | `app.py` Search tab, `analytics.Searcher`, `tagging.py` |
| Organise patents and R&D | `scripts/`, `ontology.py` (minerals, stages, org aliases) |
| Analytics and trends | Trends tab |
| Gaps, emerging areas, overlaps | `analytics.gap_table`, `analytics.emerging` |
| Collaboration opportunities | `analytics.collab_suggestions`, `org_graph` |
| Alerts | Alerts tab, `analytics.diff_snapshot` (new records, patent status changes, keyword watch) |

## Next steps
- Add the remaining minerals to `ontology.py` (full list of 30) and replace `PRIORITY` with import-dependence data.
- Swap TF-IDF for sentence-transformer embeddings and cluster-based white-space detection.
- Move storage to PostgreSQL, schedule ingestion (cron/Airflow), send email alerts.
- Add a TRL field and LLM-assisted extraction for project pages.

Run `python tests/smoke_test.py` after changing analytics code.
