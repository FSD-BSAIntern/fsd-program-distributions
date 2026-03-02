# config.py
# Edit DATA_PATH to point to your local extract (CSV or XLSX).
# Example: r"C:\Users\Isaiah\Downloads\orders_extract.xlsx"
DATA_PATH = r"O:\Business Systems Analyst\Projects\CC_Isaiah De La Rosa\Program Tier Cost Project\PCMapp\ProgramDistribution-idlrOG.csv"

# Column names expected in the dataset (exact, case-sensitive).
COL_DATE = "Date"
COL_FISCAL_YEAR = "Fiscal Year"
COL_BILL_TO_AGENCY = "Bill-to Agency"
COL_REGION = "Geographical Location Code"
COL_HH_CODE = "FBC Size Code"
COL_GROSS_WEIGHT = "Gross Weight"

# Optional columns (used only for display / future filters)
COL_CITY = "City"
COL_ZIP = "ZIP Code"

# HH buckets
HH_BUCKETS = [
    ("XS", 1, 50),
    ("S", 51, 150),
    ("M", 151, 300),
    ("L", 301, 600),
    ("XL", 601, float("inf")),
]
