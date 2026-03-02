# narrative.py
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from charts import period_label


def _fmt_pct(x) -> str:
    if pd.isna(x):
        return "NA"
    if np.isinf(x):
        return "∞"
    return f"{x*100:.1f}%"


def build_narrative(df: pd.DataFrame, granularity: str, include_prior: bool) -> str:
    # df: Table E (per entity-period)
    lines: List[str] = []

    for entity_id, g in df.groupby("entity_id"):
        g = g.sort_values("period_key").copy()
        total = float(g["lbs"].sum())
        avg = float(g["lbs"].mean()) if len(g) else 0.0
        flag_count = int(g["flag_pop_20"].sum()) if "flag_pop_20" in g.columns else 0

        lines.append(f"{entity_id}")
        lines.append(f"- Total lbs (selected range): {total:,.0f}")
        lines.append(f"- Avg lbs per period: {avg:,.0f}")
        lines.append(f"- Flagged periods (±20% PoP): {flag_count}")

        # Biggest increase/decrease (PoP%)
        if "pop_delta_pct" in g.columns:
            gg = g.dropna(subset=["pop_delta_pct"]).copy()
            if len(gg) > 0:
                inc = gg.loc[gg["pop_delta_pct"].idxmax()]
                dec = gg.loc[gg["pop_delta_pct"].idxmin()]

                lines.append(
                    f"- Largest PoP increase: {period_label(granularity, inc['period_key'])} "
                    f"({inc['pop_delta_lbs']:,.0f} lbs, {_fmt_pct(inc['pop_delta_pct'])})"
                )
                lines.append(
                    f"- Largest PoP decrease: {period_label(granularity, dec['period_key'])} "
                    f"({dec['pop_delta_lbs']:,.0f} lbs, {_fmt_pct(dec['pop_delta_pct'])})"
                )

        # Call out flagged outliers
        flagged = g[g["flag_pop_20"] == True] if "flag_pop_20" in g.columns else g.iloc[0:0]
        if len(flagged) > 0:
            lines.append("- Outliers:")
            for _, r in flagged.iterrows():
                lines.append(
                    f"  - {period_label(granularity, r['period_key'])}: "
                    f"{r['lbs']:,.0f} lbs ({_fmt_pct(r['pop_delta_pct'])} vs prior period)"
                )

        # If prior enabled, include DiD highlight summary
        if include_prior and "did_pop_pct" in g.columns:
            gg = g.dropna(subset=["did_pop_pct"]).copy()
            if len(gg) > 0:
                did_big = gg.loc[gg["did_pop_pct"].abs().idxmax()]
                lines.append(
                    f"- Biggest YoY shift in PoP% (DiD): {period_label(granularity, did_big['period_key'])} "
                    f"({_fmt_pct(did_big['did_pop_pct'])})"
                )

        lines.append("")  # blank line between entities

    return "\n".join(lines).strip()
