"""Generate SYNTHETIC demo data so the app runs offline. Not real patents or projects.

  python scripts/make_sample_data.py            # create data/records.csv
  python scripts/make_sample_data.py --append 15  # simulate new records + patent status changes (for alerts)
"""
import argparse
import pathlib
import sys
import time

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ontology import MINERALS, STAGES  # noqa: E402

OUT = ROOT / "data" / "records.csv"
S = list(STAGES)
PHRASE = {
    "Exploration": "geochemical survey and remote sensing approach for {m} exploration",
    "Mining": "open-pit mining planning method for {m} ore bodies",
    "Beneficiation": "froth flotation and magnetic separation process for beneficiation of {m} ore",
    "Extraction & refining": "hydrometallurgy route using acid leaching and solvent extraction for {m} refining",
    "Recycling": "recycling process for {m} recovery from spent batteries and e-waste",
    "End-use": "{m} alloy and cathode materials for battery and magnet applications",
}
PRE = ["Improved", "Low-cost", "Energy-efficient", "Scalable", "Selective", "Novel"]
# Stage weights per mineral (order = Exploration, Mining, Beneficiation, Extraction, Recycling, End-use).
# Deliberately uneven so the demo shows gaps.
STAGE_W = {"Lithium": [3, 1, 2, 6, 3, 9], "Cobalt": [1, 1, 3, 5, 2, 4], "Nickel": [2, 3, 4, 6, 1, 3],
           "Rare earth elements": [3, 2, 5, 6, .3, 4], "Graphite": [2, 2, 4, 1, 1, 7], "Vanadium": [1, 1, .5, 4, 1, 2]}
MIN_W = [30, 15, 15, 20, 12, 8]
ORGS = ["CSIR-NML", "CSIR-IMMT", "IIT Bombay", "IIT Kharagpur", "IISc Bangalore", "NFTDC", "BARC", "IREL",
        "IIT (ISM) Dhanbad", "KABIL", "NMDC R&D Centre", "IIT Madras"]


def gen(n, start, rng, aff, year=None):
    mins = list(MINERALS)
    mw = np.array(MIN_W, float) / sum(MIN_W)
    rows = []
    for k in range(n):
        m = rng.choice(mins, p=mw)
        sw = np.array(STAGE_W[m], float)
        si = rng.choice(len(S), p=sw / sw.sum())
        s = S[si]
        kind = rng.choice(["patent", "paper", "project"], p=[.5, .38, .12])
        if m == "Cobalt" and s == "Recycling":
            kind = rng.choice(["paper", "patent"], p=[.9, .1])
        yrs = np.arange(2012, 2026)
        w = np.linspace(1, 3, len(yrs))
        if m == "Lithium" and s == "Recycling":
            w = np.where(yrs >= 2023, 8, .2)
        y = year or int(rng.choice(yrs, p=w / w.sum()))
        status = {"patent": rng.choice(["Published", "Under examination", "Granted", "Abandoned"], p=[.5, .25, .2, .05]),
                  "paper": "Published", "project": rng.choice(["Ongoing", "Completed"], p=[.55, .45])}[kind]
        phrase = PHRASE[s].format(m=MINERALS[m][0])
        rows.append(dict(
            id=f"SYN-{start + k:05d}", kind=kind, title=f"{rng.choice(PRE)} {phrase}",
            abstract=f"This {kind} describes a {phrase}. Results indicate higher recovery and lower energy use than conventional routes.",
            org=rng.choice(ORGS, p=aff[:, si] / aff[:, si].sum()), year=y, status=status,
            url="", source="SYNTHETIC-DEMO", is_synthetic=True))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--append", type=int, default=0)
    a = ap.parse_args()
    aff = np.random.default_rng(42).dirichlet(np.ones(len(S)) * .5, size=len(ORGS)) + .02
    OUT.parent.mkdir(exist_ok=True)
    if a.append and OUT.exists():
        df = pd.read_csv(OUT)
        rng = np.random.default_rng(int(time.time()))
        new = gen(a.append, len(df) + 1, rng, aff, year=2026)
        adv = {"Published": "Under examination", "Under examination": "Granted"}
        idx = df[(df.kind == "patent") & df.status.isin(adv)].sample(5, random_state=int(time.time()) % 1000).index
        df.loc[idx, "status"] = df.loc[idx, "status"].map(adv)
        df = pd.concat([df, new], ignore_index=True)
    else:
        df = gen(900, 1, np.random.default_rng(7), aff)
    df.to_csv(OUT, index=False)
    print(f"wrote {len(df)} records to {OUT}")
