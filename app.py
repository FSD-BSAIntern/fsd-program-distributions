# app.py
from __future__ import annotations

import io
from datetime import date
from typing import List

import pandas as pd
import numpy as np
import streamlit as st

import config
from data_prep import add_derived_fields, load_dataset, resolve_window
from aggregations import (
    filter_base,
    agg_entity_period,
    agg_entity_range,
    add_deltas,
    build_prior_fy_aligned,
    add_prior_and_did,
)
from charts import make_entity_chart, period_label
from narrative import build_narrative
from report import build_report_html


st.set_page_config(page_title="Distribution Trend Calculator", layout="wide")


def _format_pct(x) -> str:
    if pd.isna(x):
        return ""
    if x == float("inf"):
        return "∞"
    if x == float("-inf"):
        return "-∞"
    try:
        return f"{x*100:.1f}%"
    except Exception:
        return ""


def _period_label(granularity: str, period_key: pd.Timestamp) -> str:
    return period_label(granularity, period_key)


st.title("Distribution Trend Calculator")

# --- Data path ---
st.subheader("Data Source")
data_path = st.text_input("Local file path (CSV or XLSX)", value=config.DATA_PATH, placeholder=r"C:\path\to\extract.xlsx")

try:
    df_raw = load_dataset(data_path)
    df = add_derived_fields(df_raw)
    
    with st.expander("DEBUG: Gross Weight parsing", expanded=True):
        st.write("File path:", data_path)
        st.write("Rows loaded:", len(df_raw))

        # raw column before conversion is in df_raw
        raw = df_raw["Gross Weight"]
        st.write("Raw dtype:", raw.dtype)
        st.write("Raw non-null count:", int(raw.notna().sum()))

        # show examples of raw values that might break parsing
        sample_bad = raw[raw.astype(str).str.contains(",", na=False)].head(10)
        st.write("Examples with commas:", sample_bad.tolist())

        # Compare totals
        st.write("Sum of derived gross_weight:", float(df["gross_weight"].sum()))
        st.write("Count of rows where derived gross_weight == 0:", int((df["gross_weight"] == 0).sum()))
    
    # --- Product Type Bucket ---
    PT_COL = "FBC Product Type Code"
    pt_num = pd.to_numeric(df[PT_COL], errors="coerce")

    NONFOOD_CODES = {1, 2, 12, 13, 19, 20, 22}
    PRODUCE_CODES = {28}

    conditions = [
        pt_num.isin(PRODUCE_CODES),
        pt_num.isin(NONFOOD_CODES),
        ]
    
    choices = ["Produce", "Non-Food"]
    
    df["_product_type_bucket"] = np.select(
        conditions,
        choices,
        default="Non-Produce"
        )
    
    with st.expander("DEBUG: Product Type totals", expanded=True):
        st.write("Total gross_weight (no filters):", float(df["gross_weight"].sum()))
        st.dataframe(
            df.groupby(["FBC Product Type Code", "_product_type_bucket"], as_index=False)["gross_weight"].sum()
            .sort_values("gross_weight", ascending=False)
            .head(40),
            use_container_width=True,
            hide_index=True
        )
        st.dataframe(
            df.groupby("_product_type_bucket", as_index=False)["gross_weight"].sum()
            .sort_values("gross_weight", ascending=False),
            use_container_width=True,
            hide_index=True
        )

    st.caption(f"Loaded {len(df):,} rows.")
        
except Exception as e:
    st.error(str(e))
    st.stop()

# --- Controls ---
st.subheader("Report Controls")

col1, col2, col3 = st.columns([1.2, 1.2, 1.6])

with col1:
    mode = st.radio("Selected Report Level:", options=["Agency", "Region"], horizontal=True)

entity_col = "entity_agency" if mode == "Agency" else "entity_region"
entity_values = sorted(df[entity_col].dropna().astype(str).unique().tolist())

with col2:
    selected_entities = st.multiselect("Selected Agency/Region(s):", options=entity_values, default=entity_values[:1])

with col3:
    granularity = st.selectbox("Choose a Time Period to Report:", options=["Weekly", "Monthly", "Yearly"], index=0)

# --- Additional filters (Inventory Posting Group, Document Type) ---
INV_COL = "Inventory Posting Group"
DOC_COL = "Document Type"

# Inventory Posting Group options (use canonical order, include only those present)
inv_canonical = ["Donated", "Purchased", "USDA/Government"]
inv_present = [x for x in inv_canonical if x in df[INV_COL].dropna().astype(str).unique()]
selected_inv = st.multiselect(
    "Select Inventory Posting Group(s)",
    options=inv_present,
    default=inv_present,  # default = include all present
)

# Document Type options with an "Other" bucket
doc_canonical = [
    "Agency Invoice",
    "Agency Credit Memo",
    "Agency Shipment",
    "Agency Return Receipt",
    "Other",
]
doc_raw = df[DOC_COL].astype(str)
known_docs = set(doc_canonical[:-1])  # everything except "Other"
df["_doc_bucket"] = doc_raw.where(doc_raw.isin(known_docs), other="Other")
df.loc[df[DOC_COL].isna(), "_doc_bucket"] = None

doc_present = [x for x in doc_canonical if x in df["_doc_bucket"].dropna().unique()]
selected_docs = st.multiselect(
    "Select Document Type(s)",
    options=doc_present,
    default=doc_present,  # default = include all present
)

# --- Product Type filter ---
product_type_options = ["Produce", "Non-Produce", "Non-Food"]
product_types_present = product_type_options

selected_product_types = st.multiselect(
    "Select Product Type(s)",
    options=product_types_present,
    default=product_types_present,
)

if not selected_entities:
    st.error("Select at least one Agency/Region.")
    st.stop()

# Time window controls
st.subheader("Time Window")
st.caption("Select a Start and End Date for the Report. You can select a date range or \
    choose an anchor date and a number of previous (selected) periods to include.")

wcol1, wcol2, wcol3, wcol4 = st.columns([1.1, 1.1, 1.1, 1.1])

window_mode = st.radio("Time Window Type", options=["Date Range", "Anchor + Period Lookback"], horizontal=True)

min_date = pd.to_datetime(df["date"].min()).date()
max_date = pd.to_datetime(df["date"].max()).date()

if window_mode == "Date Range":
    with wcol1:
        start_d = st.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
    with wcol2:
        end_d = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)
    anchor_d = None
    lookback = None
else:
    with wcol1:
        anchor_d = st.date_input("Anchor Date", value=max_date, min_value=min_date, max_value=max_date)
    with wcol2:
        lookback = st.number_input("Previous Periods", min_value=0, max_value=260, value=3, step=1)
    start_d = None
    end_d = None

with wcol3:
    yoy_toggle = st.checkbox("Include prior fiscal year same-dates? (Does not work when already comparing years)", value=False, disabled=(granularity == "Yearly"))

# Resolve window
try:
    window = resolve_window(
        df,
        granularity=granularity,
        mode=mode,
        start_date=pd.Timestamp(start_d) if window_mode == "Date Range" else None,
        end_date=pd.Timestamp(end_d) if window_mode == "Date Range" else None,
        anchor_date=pd.Timestamp(anchor_d) if window_mode == "Anchor + Period Lookback" else None,
        lookback_periods=int(lookback) if window_mode == "Anchor + Period Lookback" else None,
    )
except Exception as e:
    st.error(str(e))
    st.stop()

# Build analysis tables
# Apply additional filters before aggregation
if selected_inv:
    df = df[df[INV_COL].astype(str).isin(set(selected_inv))]

if selected_docs:
    # Filter on the bucketed doc type
    df = df[df["_doc_bucket"].astype(str).isin(set(selected_docs))]
    
if selected_product_types:
    df = df[df["_product_type_bucket"].isin(selected_product_types)]

base = filter_base(df, mode=mode, selected_entities=selected_entities, window=window, granularity=granularity)

if len(base) == 0:
    st.warning("No rows match the selected filters and date window.")
    st.stop()

ep = agg_entity_period(base)
er = agg_entity_range(base, period_keys=window.period_keys)
epd = add_deltas(ep, er)

include_prior = bool(yoy_toggle) and granularity in ("Weekly", "Monthly")
if include_prior:
    prior = build_prior_fy_aligned(df, mode=mode, selected_entities=selected_entities, window=window, granularity=granularity)
    epd = add_prior_and_did(epd, prior)

# Join range HH metrics onto each period row
epd = epd.merge(
    er[["entity_id", "hh_median_range", "hh_median_range_bucket", "hh_max_range", "hh_max_range_bucket"]],
    on="entity_id",
    how="left",
)

# Add display columns
epd["period_label"] = epd["period_key"].apply(lambda k: _period_label(granularity, k))
epd["Flag"] = epd["flag_pop_20"].apply(lambda b: "****" if b else "")

# Format for Y1
y1_cols = [
    "entity_id",
    "period_label",
    "lbs",
    "hh_median",
    "hh_median_bucket",
    "hh_max",
    "hh_max_bucket",
    "hh_median_range",
    "hh_median_range_bucket",
    "hh_max_range",
    "hh_max_range_bucket",
    "pop_delta_lbs",
    "pop_delta_pct",
    "rng_delta_lbs",
    "rng_delta_pct",
    "Flag",
]
if include_prior:
    y1_cols += [
        "lbs_prior",
        "pop_delta_pct_prior",
        "rng_delta_pct_prior",
        "did_pop_pct",
        "did_rng_pct",
    ]

y1 = epd[y1_cols].copy()

# User-facing formatting
y1_disp = y1.copy()
for c in ["lbs", "pop_delta_lbs", "rng_delta_lbs", "lbs_prior"]:
    if c in y1_disp.columns:
        y1_disp[c] = y1_disp[c].apply(lambda x: "" if pd.isna(x) else f"{float(x):,.0f}")

for c in ["hh_median", "hh_max", "hh_median_range", "hh_max_range"]:
    if c in y1_disp.columns:
        y1_disp[c] = y1_disp[c].apply(lambda x: "" if pd.isna(x) else f"{float(x):,.0f}")

for c in ["pop_delta_pct", "rng_delta_pct", "pop_delta_pct_prior", "rng_delta_pct_prior", "did_pop_pct", "did_rng_pct"]:
    if c in y1_disp.columns:
        y1_disp[c] = y1_disp[c].apply(_format_pct)

# --- Outputs ---
st.subheader("Y1. Summary Table")
st.caption("Flag (****) triggers only on ±20% period-over-period % change (current FY).")
st.dataframe(y1_disp, use_container_width=True, hide_index=True)

st.subheader("Y2. Charts")
chart_mode = st.radio("Show charts for", options=["All selected entities", "Choose one"], horizontal=True)
chosen = None
if chart_mode == "Choose one":
    chosen = st.selectbox("Entity", options=sorted(epd["entity_id"].unique().tolist()))

chart_html_frags = []
for entity_id, g in epd.groupby("entity_id"):
    if chosen and entity_id != chosen:
        continue
    fig = make_entity_chart(g, granularity=granularity, include_prior=include_prior)
    st.markdown(f"**{entity_id}**")
    st.plotly_chart(fig, use_container_width=True)
    chart_html_frags.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))

st.subheader("Y3. Verbal Summary")
narrative = build_narrative(epd, granularity=granularity, include_prior=include_prior)
st.text(narrative)

st.subheader("Y4. Downloadable HTML Report")
inputs_summary = {
    "Report level": mode,
    "Selected entities": ", ".join(selected_entities),
    "Granularity": granularity,
    "Window start": str(window.start_date.date()),
    "Window end": str(window.end_date.date()),
    "YoY same-dates comparison": "On" if include_prior else "Off",
}

# Use unformatted y1 in report (keeps numeric columns usable if needed)
y1_report = y1.copy()
# Convert pct columns to readable strings
for c in ["pop_delta_pct", "rng_delta_pct", "pop_delta_pct_prior", "rng_delta_pct_prior", "did_pop_pct", "did_rng_pct"]:
    if c in y1_report.columns:
        y1_report[c] = y1_report[c].apply(_format_pct)

html = build_report_html(
    inputs_summary=inputs_summary,
    y1_table=y1_report,
    chart_html_fragments=chart_html_frags,
    narrative_text=narrative,
    title="Distribution Summary Report",
)

st.download_button(
    label="Download HTML report",
    data=html.encode("utf-8"),
    file_name="distribution_report.html",
    mime="text/html",
)
