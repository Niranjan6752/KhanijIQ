"""Fetch Indian-affiliated research papers on critical minerals from OpenAlex (free API).

  python scripts/ingest_openalex.py you@example.com   # OpenAlex asks for a contact email
Output: data/raw_openalex.csv  (then run scripts/build_dataset.py)
"""
import pathlib
import sys
import time

import pandas as pd
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ontology import MINERALS  # noqa: E402

API = "https://api.openalex.org/works"
TOPICS = ["extraction", "beneficiation", "recycling", "processing"]


def abstract(inv):
    """OpenAlex stores abstracts as an inverted index; rebuild the text."""
    if not inv:
        return ""
    pos = {i: w for w, idxs in inv.items() for i in idxs}
    return " ".join(pos[i] for i in sorted(pos))


def fetch(term, mailto, max_pages=2):
    cursor, out = "*", []
    for _ in range(max_pages):
        r = requests.get(API, params={
            "search": term, "per-page": 200, "cursor": cursor, "mailto": mailto,
            "filter": "authorships.institutions.country_code:IN,from_publication_date:2012-01-01"}, timeout=60)
        r.raise_for_status()
        j = r.json()
        for w in j["results"]:
            inst = [i["display_name"] for a in w.get("authorships", []) for i in a.get("institutions", [])
                    if i.get("country_code") == "IN"]
            out.append(dict(id="OA-" + w["id"].rsplit("/", 1)[-1], kind="paper", title=w.get("title") or "",
                            abstract=abstract(w.get("abstract_inverted_index")), org=inst[0] if inst else "Unknown",
                            year=w.get("publication_year"), status="Published", url=w.get("doi") or w["id"],
                            source="OpenAlex", is_synthetic=False))
        cursor = j["meta"].get("next_cursor")
        if not cursor:
            break
        time.sleep(0.2)
    return out


if __name__ == "__main__":
    mailto = sys.argv[1] if len(sys.argv) > 1 else "you@example.com"
    rows = []
    for m in MINERALS:
        for t in TOPICS:
            print("fetching", m, t)
            rows += fetch(f"{m} {t}", mailto)
    df = pd.DataFrame(rows).drop_duplicates("id")
    df.to_csv(ROOT / "data" / "raw_openalex.csv", index=False)
    print(f"saved {len(df)} papers")
