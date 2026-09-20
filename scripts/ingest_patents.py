"""Load Indian patent records from a CSV export (Lens.org, Google Patents/BigQuery, or a manual InPASS export).

  python scripts/ingest_patents.py path/to/export.csv
Output: data/raw_patents.csv. Export column names differ by source: edit CANDIDATES if the script
reports a missing column. Respect each source's terms of use.
"""
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANDIDATES = {
    "id": ["Lens ID", "publication_number", "Publication Number", "Application Number"],
    "title": ["Title", "title"],
    "abstract": ["Abstract", "abstract"],
    "org": ["Applicants", "Applicant/s", "applicant", "assignee"],
    "date": ["Publication Date", "Date Published", "publication_date", "Filing Date"],
    "status": ["Legal Status", "legal_status", "Status"],
    "url": ["URL", "Lens URL"],
    "country": ["Jurisdiction", "country_code"],
}


def pick(df, key):
    for c in CANDIDATES[key]:
        if c in df.columns:
            return df[c]
    return None


def to_year(s):
    s = s.astype(str).str.replace(r"\.0$", "", regex=True)
    dt = pd.to_datetime(s, format="%Y%m%d", errors="coerce").fillna(pd.to_datetime(s, errors="coerce"))
    return dt.dt.year


if __name__ == "__main__":
    src = pd.read_csv(sys.argv[1])
    cols = {k: pick(src, k) for k in CANDIDATES}
    missing = [k for k in ("id", "title", "org", "date") if cols[k] is None]
    if missing:
        sys.exit(f"Missing columns for {missing}. Found: {list(src.columns)}")
    out = pd.DataFrame({
        "id": "PAT-" + cols["id"].astype(str), "kind": "patent", "title": cols["title"],
        "abstract": cols["abstract"] if cols["abstract"] is not None else "",
        "org": cols["org"].astype(str).str.split(r"[;|]").str[0].str.strip(),
        "year": to_year(cols["date"]),
        "status": cols["status"] if cols["status"] is not None else "Published",
        "url": cols["url"] if cols["url"] is not None else "", "source": "Patent export", "is_synthetic": False})
    if cols["country"] is not None:
        out = out[cols["country"].astype(str).str.upper().isin(["IN", "INDIA"])]
    out.to_csv(ROOT / "data" / "raw_patents.csv", index=False)
    print(f"saved {len(out)} patents")
