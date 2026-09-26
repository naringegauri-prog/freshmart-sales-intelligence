"""Every cleaning rule as a function; QualityLog records what each one did."""
import pandas as pd

class QualityLog:
    def __init__(self): self.rows = []
    def add(self, problem, affected, fix, why): self.rows.append({"problem": problem, "rows_affected": int(affected), "fix": fix, "why": why})
    def to_frame(self): return pd.DataFrame(self.rows)

def clean_products(products, log):
    p = products.copy()
    # TODO: product_name whitespace; cost_price > unit_price -> flag column margin_ok. Log each rule.
    ws_count = (p["product_name"] != p["product_name"].astype(str).str.strip()).sum()
    p["product_name"] = p["product_name"].astype(str).str.strip()
    log.add("whitespace in product_name", ws_count, "strip whitespace", "Clean up names")

    bad_margin = p["cost_price"] > p["unit_price"]
    p["margin_ok"] = ~bad_margin
    log.add("cost exceeds unit price", bad_margin.sum(), "set margin_ok False", "Cost price cannot exceed unit price")
    return p

def clean_sales(sales, products, stores, log):
    df = sales.copy()
    # TODO, in this order, logging each: duplicates -> unit_price text to number -> dates (two formats!)
    #       -> negative qty -> unknown product_id -> unknown store_id -> missing discount_pct
    # Then derive: net_price = unit_price * (1 - discount_pct/100); revenue = net_price * qty
    n = len(df); df = df.drop_duplicates(); log.add("duplicates", n - len(df), "drop duplicates", "Remove repeated transactions")
    
    df["unit_price"] = pd.to_numeric(df["unit_price"].astype(str).str.replace("$", "", regex=False).str.strip(), errors="coerce")
    n = len(df); df = df.dropna(subset=["unit_price"]); log.add("unit_price text", n - len(df), "convert to numeric", "Ensure price is float")
    
    df["sale_date"] = pd.to_datetime(df["sale_date"], format="mixed", errors="coerce")
    n = len(df); df = df.dropna(subset=["sale_date"]); log.add("invalid dates", n - len(df), "parse dates", "Standardize date formats")
    
    n = len(df); df = df[df["qty"] >= 0]; log.add("negative qty", n - len(df), "remove negative qty", "Qty must be non-negative")
    
    n = len(df); df = df[df["product_id"].isin(products["product_id"])]; log.add("unknown product_id", n - len(df), "remove orphan records", "Match products table")
    
    n = len(df); df = df[df["store_id"].isin(stores["store_id"])]; log.add("unknown store_id", n - len(df), "remove orphan records", "Match stores table")
    
    missing_disc = df["discount_pct"].isna().sum()
    df["discount_pct"] = df["discount_pct"].fillna(0)
    log.add("missing discount_pct", missing_disc, "fill with 0", "Default to 0% discount")

    df["net_price"] = df["unit_price"] * (1 - df["discount_pct"] / 100)
    df["revenue"] = df["net_price"] * df["qty"]
    return df.reset_index(drop=True)