"""Merge data/raw_*.csv plus your curated data/projects.csv into data/records.csv (clean, de-duplicated)."""
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ontology import canon_org  # noqa: E402

COLS = ["id", "kind", "title", "abstract", "org", "year", "status", "url", "source", "is_synthetic"]

if __name__ == "__main__":
    files = sorted((ROOT / "data").glob("raw_*.csv")) + [ROOT / "data" / "projects.csv"]
    frames = [pd.read_csv(f) for f in files if f.exists()]
    if not frames:
        sys.exit("Nothing to merge. Run an ingest script first.")
    df = pd.concat(frames, ignore_index=True).reindex(columns=COLS)
    df["org"] = df.org.map(canon_org)
    df = df.drop_duplicates("id").drop_duplicates(["title", "org"])
    df.to_csv(ROOT / "data" / "records.csv", index=False)
    print(f"wrote {len(df)} records from {len(frames)} files")
