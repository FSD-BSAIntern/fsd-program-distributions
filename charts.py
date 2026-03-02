# charts.py
from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go


def period_label(granularity: str, period_key: pd.Timestamp) -> str:
    if granularity == "Weekly":
        start = pd.Timestamp(period_key).date()
        end = (pd.Timestamp(period_key) + pd.Timedelta(days=6)).date()
        return f"{start} to {end}"
    if granularity == "Monthly":
        return pd.Timestamp(period_key).strftime("%Y-%m")
    if granularity == "Yearly":
        # period_key is FY start
        fy = pd.Timestamp(period_key).year + 1  # FY year = start year + 1
        return f"FY {fy}"
    return str(period_key)


def make_entity_chart(df_entity: pd.DataFrame, granularity: str, include_prior: bool) -> go.Figure:
    df_entity = df_entity.sort_values("period_key").copy()
    x = [period_label(granularity, k) for k in df_entity["period_key"]]

    fig = go.Figure()

    # Bars: current
    fig.add_trace(
        go.Bar(
            x=x,
            y=df_entity["lbs"],
            name="Current FY",
        )
    )

    # Optional prior line
    if include_prior and "lbs_prior" in df_entity.columns:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=df_entity["lbs_prior"],
                mode="lines+markers",
                name="Prior FY (same dates)",
            )
        )

    # Mark flagged bars (PoP >= 20%)
    if "flag_pop_20" in df_entity.columns:
        flagged = df_entity[df_entity["flag_pop_20"] == True]
        if len(flagged) > 0:
            fx = [period_label(granularity, k) for k in flagged["period_key"]]
            fy = flagged["lbs"].tolist()
            fig.add_trace(
                go.Scatter(
                    x=fx,
                    y=fy,
                    mode="markers",
                    name="Flag (±20% PoP)",
                )
            )

    fig.update_layout(
        height=420,
        margin=dict(l=30, r=20, t=30, b=60),
        xaxis_title="Period",
        yaxis_title="Lbs Distributed",
        legend_title="Series",
    )
    return fig
