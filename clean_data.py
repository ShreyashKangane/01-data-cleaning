"""
Data Cleaning Script
Dataset: messy_sample_data.csv (small sample e-commerce order data)
Tool: pandas

Each cleaning step below is documented with what was found and what was done.
"""
import pandas as pd
import numpy as np

log = []  # (step, description, detail)

df = pd.read_csv("messy_sample_data.csv", dtype=str)
log.append(("Load", "Loaded raw CSV", f"{len(df)} rows, {len(df.columns)} columns"))

# ---- Step 1: Trim whitespace from text fields ----
text_cols = ["Customer Name", "Email", "Region", "Product"]
before = df[text_cols].copy()
for c in text_cols:
    df[c] = df[c].str.strip()
changed = (before != df[text_cols]).any(axis=1).sum()
log.append(("Trim whitespace", f"Stripped leading/trailing spaces in {text_cols}", f"{changed} rows affected"))

# ---- Step 2: Standardize text casing ----
df["Customer Name"] = df["Customer Name"].str.title()
df["Region"] = df["Region"].str.title()
df["Email"] = df["Email"].str.lower()
log.append(("Standardize casing", "Title-cased names/regions, lower-cased emails",
            "e.g. 'maria garcia' -> 'Maria Garcia', 'MARIA.G@email.com' -> 'maria.g@email.com'"))

# ---- Step 3: Standardize date formats ----
def parse_date(v):
    if pd.isna(v) or v == "":
        return pd.NaT
    v = v.replace("/", "-")
    return pd.to_datetime(v, errors="coerce")

raw_missing_dates = (df["Order Date"].isna() | (df["Order Date"] == "")).sum()
df["Order Date"] = df["Order Date"].apply(parse_date)
missing_after_parse = df["Order Date"].isna().sum()
log.append(("Standardize dates", "Parsed mixed formats (YYYY-MM-DD, MM/DD/YYYY, YYYY/MM/DD) into one date type",
            f"{missing_after_parse} rows still missing a date"))

# ---- Step 4: Handle missing values ----
missing_qty = df["Quantity"].isna().sum() + (df["Quantity"] == "").sum()
df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
median_qty = df["Quantity"].median()
df["Quantity"] = df["Quantity"].fillna(median_qty)
log.append(("Fill missing Quantity", f"{missing_qty} rows had missing Quantity",
            f"Filled with median quantity ({median_qty:.0f})"))

missing_region = (df["Region"].isna() | (df["Region"] == "")).sum()
df["Region"] = df["Region"].replace("", np.nan)
df["Region"] = df["Region"].fillna("Unknown")
log.append(("Fill missing Region", f"{missing_region} rows had missing Region", "Filled with 'Unknown'"))

missing_date_final = df["Order Date"].isna().sum()
if missing_date_final:
    df["Order Date"] = df["Order Date"].fillna(pd.NaT)
    log.append(("Flag missing Order Date", f"{missing_date_final} rows still have no date",
                "Left blank and flagged rather than guessed, since no reliable estimate exists"))

# ---- Step 5: Fix data types ----
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
df["Order ID"] = pd.to_numeric(df["Order ID"], errors="coerce").astype("Int64")
df["Quantity"] = df["Quantity"].astype(int)
log.append(("Fix data types", "Converted Order ID/Quantity to integers, Price to numeric, Order Date to datetime",
            "Ensures totals and sorting work correctly"))

# ---- Step 6: Remove duplicate records ----
before_n = len(df)
df = df.drop_duplicates(subset=["Customer Name", "Email", "Product", "Order Date", "Quantity", "Price"], keep="first")
dupes_removed = before_n - len(df)
log.append(("Remove duplicates", "Dropped exact repeat orders (same customer, product, date, qty, price)",
            f"{dupes_removed} duplicate rows removed"))

# ---- Step 7: Add calculated column ----
df["Total"] = (df["Quantity"] * df["Price"]).round(2)
log.append(("Add Total column", "Calculated Total = Quantity x Price", "New column added for downstream analysis"))

# ---- Step 8: Reorder & reset index ----
df = df[["Order ID","Customer Name","Email","Region","Product","Quantity","Price","Total","Order Date"]]
df = df.sort_values("Order ID").reset_index(drop=True)
log.append(("Reorder & sort", "Reordered columns logically and sorted by Order ID", f"Final: {len(df)} clean rows"))

df.to_csv("cleaned_sample_data.csv", index=False)

log_df = pd.DataFrame(log, columns=["Step", "Action Taken", "Detail"])
log_df.to_csv("cleaning_log.csv", index=False)

print(log_df.to_string(index=False))
print("\nCleaned dataset saved:", len(df), "rows")
