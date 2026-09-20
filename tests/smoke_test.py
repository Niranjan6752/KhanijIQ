"""Quick check that data -> tagging -> analytics works. Run from the project root: python tests/smoke_test.py"""
import pathlib
import subprocess
import sys

import pandas as pd

sys.path.insert(0, ".")
import analytics as A  # noqa: E402
import tagging  # noqa: E402

subprocess.run([sys.executable, "scripts/make_sample_data.py"], check=True)
df = tagging.tag_df(pd.read_csv("data/records.csv"))
df = df[df.minerals.map(len) > 0]
assert len(df) > 500, "tagging lost too many records"
assert not A.gap_table(df).empty and not A.emerging(df).empty
assert not A.collab_suggestions(df).empty and A.org_graph(df).number_of_nodes() > 0
assert not A.Searcher(df).query("lithium recycling").empty
print("smoke test passed:", len(df), "records")
