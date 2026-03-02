## Step by Step Process:



##### Step 1. 

Define the data model + transformation rules (time periods, fiscal year logic, HH-size parsing/bucketing, and delta definitions).



##### Step 2. 

Build the aggregation engine (filter X0/X1, group by X2, compute lbs + HH metrics, compute deltas, compute flags).



##### Step 3. 

Build the UI in VS Code (likely Streamlit): selectors for X0–X3.5, validation, and displaying Y1/Y2/Y3.



##### Step 4. 

Generate the downloadable report (render tables + plots + narrative into HTML/PDF).



##### Step 5. 

QA with edge cases (missing weeks, single-period selections, multi-select entities, weird HH codes, zero baselines).



### Checklist: 



##### Step 1. - Parameter Definitions and Objective Funciton

1. Fiscal Year Rule - If date month >= 7, FY = calendar year + 1, else FY = calendar year
2. Weekly period start - Monday denotes week beginning, Sunday is week end
3. HH size buckets - where "67D 130P" -> 130 HHs. Numbers are treated as numbers, there are no other special formats to parse through. Range thresholds are as follows: XS = 1-50, S = 51-150, M = 151-300, L = 301-600, XL = 601+
4. There should be two metrics, the median HH size and size bucket, in addition to the maximum hh size and bucked in the selected range.
5. When x3.5 is on, then the period over period delta and range-average delta should be computed twice, once for the current fiscal year, and again for the previous fiscal year. Thus I should have four metrics, one for each fiscal year for period over period and range-average, to compare the differences in differences YoY. lets lets 



##### Step 2. - Data Preparation

1. Table A: Base Filtered Orders - one clean row per order with new columns and standardized values. Filters from chosen X0, x1, and X3 are applied
2. Table B: Entity-Period Aggregates - One row per (entity\_id, period\_key) for the selected window, for the current FY periods included in that window. Data for figures Y1 and Y2
3. Table C: Entity-Range Aggregates - The selected range HH stats and baseline for deltas in lbs dist.
4. Table D: Entity Period Aggregates (Previous FY CONDITIONAL) - only created when X2 is weekly or monthly and user selects to compare previous FY same-dates. Identical to Table B
5. Table E: Delta Metrics - Per Entity Period - One row per (entity\_id, period\_key) in the selected window (aligned axis). Contains deltas for current FY, and if X3.5 is ON, also prior FY deltas and DiD deltas.



##### Step 3. - UI and App Structure

0\. Base: Streamlit app in Python

1. Data Source: Temporary a File Upload, with goal to move to local file path + Skip to config
2. Report Controls: x0 is a Region or Agency choice, x1 is a multiselect list populated by the dataset (either geographical region or bill to agency) 1 select min, max of 10 at once. x2 is a selectbox of Weekly/Monthly/Yearly. X3 is either date range mode or date anchor plus lookback range. x3.5 is a toggle checkbox " include prior fiscal year same-dates for comparison - hidden when x2 is yearly. 

##### Step 4. - Project Layout

app.py (Streamlit UI; orchestrates inputs → calls analysis → renders outputs → triggers HTML export)

config.py (DATA_PATH, column name mappings, optional defaults)

data_prep.py (load dataset, standardize column types, parse HH size, compute FY and period keys)

aggregations.py (build Tables B/C/D and Table E delta metrics)

charts.py (build per-entity bar/line charts from Table E)

narrative.py (generate Y3 text from Table E + range stats)

report.py (assemble HTML string with embedded table and chart HTML, plus inputs summary)

requirements.txt





