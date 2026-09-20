"""KhanijIQ: Indian patents + R&D intelligence for critical minerals. Run: streamlit run app.py"""
from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analytics as A
import tagging
from ontology import MINERALS, STAGES

st.set_page_config(page_title="KhanijIQ: critical minerals tracker", layout="wide")
DATA = Path("data/records.csv")

if not DATA.exists():
    st.error("No data yet. Run `python scripts/make_sample_data.py` for demo data, or use the ingest scripts "
             "and then `python scripts/build_dataset.py`.")
    st.stop()


@st.cache_data
def load(mtime):
    df = pd.read_csv(DATA)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"]).astype({"year": int})
    df = tagging.tag_df(df)
    return df[df.minerals.map(len) > 0].reset_index(drop=True)


df = load(DATA.stat().st_mtime)
st.title("KhanijIQ")
st.caption("Indian patents and R&D activity for critical minerals, in one view.")
if df["is_synthetic"].astype(str).str.lower().eq("true").any():
    st.warning("This dataset contains synthetic demo records. Replace them with real data before drawing conclusions.")

# ---- sidebar filters ------------------------------------------------------------------------
st.sidebar.header("Filters")
sel_min = st.sidebar.multiselect("Minerals", list(MINERALS), default=list(MINERALS))
sel_kind = st.sidebar.multiselect("Record type", ["patent", "paper", "project"], default=["patent", "paper", "project"])
y0, y1 = int(df.year.min()), int(df.year.max())
yr = st.sidebar.slider("Years", y0, y1, (y0, y1)) if y0 < y1 else (y0, y1)
f = df[df.kind.isin(sel_kind) & df.year.between(*yr) & df.minerals.map(lambda m: bool(set(m) & set(sel_min)))]
if f.empty:
    st.info("No records match these filters. Widen the year range or add minerals.")
    st.stop()

c = st.columns(4)
c[0].metric("Records", len(f))
c[1].metric("Patents", int(f.kind.eq("patent").sum()))
c[2].metric("Organisations", f.org.nunique())
c[3].metric("Minerals covered", len({m for ms in f.minerals for m in ms} & set(sel_min)))

tabs = st.tabs(["Search", "Trends", "Gaps and emerging areas", "Organisations", "Alerts"])

# ---- search ---------------------------------------------------------------------------------
with tabs[0]:
    q = st.text_input("Search by keyword, mineral or process", placeholder="e.g. lithium brine extraction")
    stage_f = st.multiselect("Value-chain stage", list(STAGES))
    res = A.Searcher(f).query(q, k=500)
    if stage_f:
        res = res[res.stages.map(lambda s: bool(set(s) & set(stage_f)))]
    st.write(f"{len(res)} results")
    show = res.assign(minerals=res.minerals.map(", ".join), stages=res.stages.map(", ".join))
    st.dataframe(show[["kind", "title", "org", "year", "status", "minerals", "stages", "url"]].head(200),
                 hide_index=True, column_config={"url": st.column_config.LinkColumn("Link")})

# ---- trends ---------------------------------------------------------------------------------
with tabs[1]:
    yearly = f.groupby(["year", "kind"]).size().reset_index(name="records")
    st.plotly_chart(px.bar(yearly, x="year", y="records", color="kind", title="Activity by year"))
    left, right = st.columns(2)
    orgs = A.top_orgs(f)
    fig = px.bar(orgs, x="records", y="org", color="kind", orientation="h", title="Leading organisations")
    fig.update_yaxes(categoryorder="total ascending")
    left.plotly_chart(fig)
    by_min = A.explode_cells(f).drop_duplicates(["id", "minerals"]).groupby(["minerals", "kind"]).size()
    right.plotly_chart(px.bar(by_min.reset_index(name="records"), x="minerals", y="records", color="kind",
                              title="Records by mineral"))

# ---- gaps -----------------------------------------------------------------------------------
with tabs[2]:
    g = A.gap_table(f, sel_min)
    label = {"total": "All records", "patents": "Patents only", "rd": "Research and projects only"}
    metric = st.radio("Heatmap shows", list(label), format_func=label.get, horizontal=True)
    piv = g.pivot(index="mineral", columns="stage", values=metric).reindex(index=sel_min, columns=list(STAGES))
    st.plotly_chart(px.imshow(piv, text_auto=True, aspect="auto", color_continuous_scale="Teal",
                              title="Mineral by value-chain stage"))
    st.subheader("Where the gaps are")
    st.caption("Gap score = strategic priority / (1 + records in the cell). Priorities in ontology.py are placeholders.")
    st.dataframe(g.head(15)[["mineral", "stage", "patents", "rd", "orgs", "priority", "gap_score", "signal"]],
                 hide_index=True)
    st.subheader("Emerging areas")
    st.caption("Cells with the fastest growth in the last 3 years versus the 3 years before.")
    st.dataframe(A.emerging(f).head(10), hide_index=True)

# ---- organisations --------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Suggested collaborations")
    st.caption("Organisations working on the same mineral with strengths in different stages.")
    st.dataframe(A.collab_suggestions(f), hide_index=True)
    G = A.org_graph(f)
    pos = nx.spring_layout(G, seed=7, weight="weight")
    ex, ey = [], []
    for a, b in G.edges:
        ex += [pos[a][0], pos[b][0], None]
        ey += [pos[a][1], pos[b][1], None]
    fig = go.Figure([
        go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=0.6, color="#9aa7ad"), hoverinfo="none"),
        go.Scatter(x=[pos[n][0] for n in G], y=[pos[n][1] for n in G], mode="markers+text", text=list(G),
                   textposition="top center", marker=dict(size=[8 + 2 * G.nodes[n]["n"] ** 0.5 for n in G],
                                                          color="#1F6F78"),
                   hovertext=[f"{n}: {G.nodes[n]['n']} records" for n in G], hoverinfo="text")])
    fig.update_layout(showlegend=False, xaxis_visible=False, yaxis_visible=False, title="Organisation overlap network",
                      margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig)

# ---- alerts ---------------------------------------------------------------------------------
with tabs[4]:
    st.write("Compare today's data with a saved baseline to see what is new or has changed status.")
    new, changed = A.diff_snapshot(df)
    if new is None:
        st.info("No baseline yet. Save one now, then re-run ingestion (or `make_sample_data.py --append 15`) to see alerts.")
    else:
        watch = st.text_input("Watch keywords (comma-separated, optional)")
        words = [w.strip().lower() for w in watch.split(",") if w.strip()]
        if words:
            text = (new.title.fillna("") + " " + new.abstract.fillna("")).str.lower()
            new = new[text.map(lambda t: any(w in t for w in words))]
        a, b = st.columns(2)
        a.metric("New records", len(new))
        b.metric("Status changes", len(changed))
        cols = ["kind", "title", "org", "year", "status"]
        st.subheader("New since baseline")
        st.dataframe(new[cols], hide_index=True)
        st.subheader("Status changed")
        st.dataframe(changed[cols], hide_index=True)
    if st.button("Save current data as baseline"):
        A.save_snapshot(df)
        st.rerun()
