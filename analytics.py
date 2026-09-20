"""Search, trends, gap analysis, emerging areas, collaboration suggestions, alerts."""
import json
from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from ontology import MINERALS, PRIORITY, STAGES

SNAPSHOT = Path("data/snapshot.json")


def explode_cells(df):
    """One row per (record, mineral, stage) cell."""
    return df.explode("minerals").explode("stages").dropna(subset=["minerals", "stages"])


class Searcher:
    """TF-IDF keyword search (swap for sentence-transformer embeddings later)."""

    def __init__(self, df):
        self.df = df.reset_index(drop=True)
        self.vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.X = self.vec.fit_transform(self.df.title.fillna("") + " " + self.df.abstract.fillna(""))

    def query(self, q, k=100):
        if not q.strip():
            return self.df.sort_values("year", ascending=False).head(k)
        score = (self.X @ self.vec.transform([q]).T).toarray().ravel()
        out = self.df.assign(score=score)
        return out[out.score > 0].sort_values("score", ascending=False).head(k)


def top_orgs(df, n=15):
    top = df.org.value_counts().head(n).index
    return df[df.org.isin(top)].groupby(["org", "kind"]).size().reset_index(name="records")


def gap_table(df, minerals=None):
    """Mineral x stage cells with a strategic gap score and a plain-language signal."""
    minerals = list(minerals or MINERALS)
    d = explode_cells(df).assign(is_patent=lambda x: x.kind.eq("patent"))
    g = d.groupby(["minerals", "stages"]).agg(patents=("is_patent", "sum"), total=("id", "count"),
                                              orgs=("org", "nunique"))
    idx = pd.MultiIndex.from_product([minerals, list(STAGES)], names=["minerals", "stages"])
    g = g.reindex(idx, fill_value=0).reset_index().rename(columns={"minerals": "mineral", "stages": "stage"})
    g["patents"] = g.patents.astype(int)
    g["rd"] = g.total - g.patents
    g["priority"] = g.mineral.map(PRIORITY)
    g["gap_score"] = (g.priority / (1 + g.total)).round(3)
    low, crowded = max(2, g.total.quantile(.2)), max(6, g.orgs.quantile(.8))  # relative thresholds
    g["signal"] = np.select(
        [g.total <= low, (g.rd >= 5) & (g.rd >= 3 * (g.patents + 1)), g.orgs >= crowded],
        ["White space", "Research not yet patented", "Crowded: check overlap"],
        default="Balanced",
    )
    return g.sort_values("gap_score", ascending=False).reset_index(drop=True)


def emerging(df, window=3):
    """Cells whose activity in the last `window` years grew versus the `window` years before."""
    d = explode_cells(df)
    if d.empty:
        return pd.DataFrame()
    y = int(d.year.max())
    rec = d[d.year > y - window].groupby(["minerals", "stages"]).size().rename("recent")
    pri = d[(d.year <= y - window) & (d.year > y - 2 * window)].groupby(["minerals", "stages"]).size().rename("prior")
    t = pd.concat([pri, rec], axis=1).fillna(0)
    t["growth_x"] = ((t.recent + 1) / (t.prior + 1)).round(2)
    t = t[t.recent >= 3].sort_values("growth_x", ascending=False).reset_index()
    return t.rename(columns={"minerals": "mineral", "stages": "stage"}).astype({"recent": int, "prior": int})


def collab_suggestions(df, min_activity=3, top=15):
    """Pairs of organisations active on the same mineral but strong in different stages."""
    d = explode_cells(df)
    prof = d.groupby(["org", "minerals", "stages"]).size().unstack("stages", fill_value=0)
    prof = prof.reindex(columns=list(STAGES), fill_value=0)
    stage_names = list(STAGES)
    rows = []
    for m, sub in prof.groupby(level="minerals"):
        sub = sub.droplevel("minerals")
        sub = sub[sub.sum(axis=1) >= min_activity]
        orgs, V = list(sub.index), sub.values.astype(float)
        for i, j in combinations(range(len(orgs)), 2):
            a, b = V[i], V[j]
            cos = a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
            covered = (np.maximum(a, b) > 0).sum() / len(stage_names)
            rows.append(dict(mineral=m, org_a=orgs[i], strength_a=stage_names[a.argmax()],
                             org_b=orgs[j], strength_b=stage_names[b.argmax()],
                             complementarity=round((1 - cos) * covered, 3)))
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out[out.strength_a != out.strength_b]
    return out.sort_values("complementarity", ascending=False).head(top).reset_index(drop=True)


def org_graph(df, top=30, min_shared=2):
    """Organisations linked when they work on the same mineral/stage cells."""
    d = explode_cells(df)
    cells = d.assign(cell=d.minerals + " | " + d.stages).groupby("org")["cell"].agg(set)
    n = df.org.value_counts().head(top)
    G = nx.Graph()
    for o, c in n.items():
        G.add_node(o, n=int(c))
    for a, b in combinations(n.index, 2):
        shared = len(cells.get(a, set()) & cells.get(b, set()))
        if shared >= min_shared:
            G.add_edge(a, b, weight=shared)
    return G


# ---- alerts: compare current data with a saved baseline -------------------------------------
def save_snapshot(df):
    SNAPSHOT.parent.mkdir(exist_ok=True)
    SNAPSHOT.write_text(json.dumps({i: (s if pd.notna(s) else "") for i, s in zip(df.id, df.status)}))


def diff_snapshot(df):
    """Returns (new_records, status_changed_records), or (None, None) when no baseline exists."""
    if not SNAPSHOT.exists():
        return None, None
    snap = json.loads(SNAPSHOT.read_text())
    new = df[~df.id.isin(snap)]
    mask = [(i in snap and snap[i] != (s if pd.notna(s) else "")) for i, s in zip(df.id, df.status)]
    return new, df[mask]
