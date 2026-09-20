"""Ontology-based tagging: which minerals and value-chain stages does a record cover?"""
import re

import pandas as pd

from ontology import MINERALS, STAGES


def _compile(d):
    return {k: re.compile(r"\b(?:%s)\b" % "|".join(map(re.escape, v)), re.I) for k, v in d.items()}


_M, _S = _compile(MINERALS), _compile(STAGES)


def tag_text(text):
    text = text or ""
    return [k for k, r in _M.items() if r.search(text)], [k for k, r in _S.items() if r.search(text)]


def tag_df(df: pd.DataFrame) -> pd.DataFrame:
    text = df["title"].fillna("") + ". " + df["abstract"].fillna("")
    tags = text.map(tag_text)
    out = df.copy()
    out["minerals"] = tags.map(lambda t: t[0])
    out["stages"] = tags.map(lambda t: t[1])
    return out
