"""Analysis functions. Each returns a DataFrame; each is timed."""
import time, functools
import numpy as np, pandas as pd

def timed(fn):
    """TODO: decorator that prints how long fn took. Use functools.wraps."""
    # TODO: decorator that prints how long fn took. Use functools.wraps.
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        t1 = time.perf_counter()
        print(f"[{fn.__name__}] took {t1 - t0:.4f}s")
        return result
    return wrapper

@timed
def top_margin(sales, products, store_id=None, n=10):
    """Top n products by (net_price - cost_price) * qty. Exclude rows where margin_ok is False."""
    # TODO: Exclude rows where margin_ok is False.
    df = sales.copy()
    if "margin_ok" in df.columns:
        df = df[df["margin_ok"] != False]

    # TODO: Filter by store_id if provided.
    if store_id is not None:
        df = df[df["store_id"] == store_id]

    # TODO: Calculate net_price, margin = (net_price - cost_price) * qty, and return top n.
    merged = df.merge(products, on="product_id", how="inner", suffixes=("", "_prod"))
    disc = merged["discount_pct"] if "discount_pct" in merged.columns else 0.0
    net_price = merged["unit_price"] * (1.0 - disc / 100.0)
    merged["margin"] = (net_price - merged["cost_price"]) * merged["qty"]

    group_cols = [c for c in ["product_id", "product_name", "category"] if c in merged.columns]
    res = merged.groupby(group_cols, as_index=False)["margin"].sum()
    return res.sort_values(by="margin", ascending=False).head(n).reset_index(drop=True)

@timed
def promo_lift(sales, promotions, rng=None, n_perm=1000):
    """For each promotion: qty/day in the promo window vs same weekdays in the 8 weeks before; permutation p-value."""
    # TODO: For each promotion: qty/day in the promo window vs same weekdays in the 8 weeks before; permutation p-value.
    if rng is None:
        rng = np.random.default_rng(42)

    df = sales.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["weekday"] = df["sale_date"].dt.dayofweek

    records = []
    for _, promo in promotions.iterrows():
        p_id = promo["promo_id"]
        prod_id = promo["product_id"]
        store_id = promo["store_id"]
        start = pd.to_datetime(promo["start_date"])
        end = pd.to_datetime(promo["end_date"])

        # 8 weeks (56 days) prior baseline window
        base_start = start - pd.Timedelta(days=56)
        base_end = start - pd.Timedelta(days=1)

        sub = df[(df["product_id"] == prod_id) & (df["store_id"] == store_id)]

        promo_dates = pd.date_range(start, end)
        promo_days = set(promo_dates.dayofweek)

        base_dates = [d for d in pd.date_range(base_start, base_end) if d.dayofweek in promo_days]

        promo_sub = sub[(sub["sale_date"] >= start) & (sub["sale_date"] <= end)]
        promo_daily = promo_sub.groupby("sale_date")["qty"].sum().reindex(promo_dates, fill_value=0).values

        base_sub = sub[(sub["sale_date"] >= base_start) & (sub["sale_date"] <= base_end) & (sub["weekday"].isin(promo_days))]
        base_daily = base_sub.groupby("sale_date")["qty"].sum().reindex(base_dates, fill_value=0).values if base_dates else np.array([0])

        promo_rate = float(np.mean(promo_daily)) if len(promo_daily) > 0 else 0.0
        base_rate = float(np.mean(base_daily)) if len(base_daily) > 0 else 0.0
        diff = promo_rate - base_rate

        n1, n2 = len(promo_daily), len(base_daily)
        if n1 > 0 and n2 > 0 and (promo_rate > 0 or base_rate > 0):
            combined = np.concatenate([promo_daily, base_daily])
            sim = rng.permuted(np.tile(combined, (n_perm, 1)), axis=1)
            sim_diffs = sim[:, :n1].mean(axis=1) - sim[:, n1:].mean(axis=1)
            p_val = float(np.mean(np.abs(sim_diffs) >= np.abs(diff)))
        else:
            p_val = 1.0

        records.append({
            "promo_id": p_id,
            "product_id": prod_id,
            "store_id": store_id,
            "promo_qty_per_day": promo_rate,
            "baseline_qty_per_day": base_rate,
            "lift": diff,
            "p_value": p_val
        })

    return pd.DataFrame(records)

@timed
def patterns(sales, products):
    """Return two pivot tables: category x weekday units, category x month units."""
    # TODO: Return two pivot tables: category x weekday units, category x month units.
    df = sales.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    merged = df.merge(products[["product_id", "category"]], on="product_id", how="left")

    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    merged["weekday"] = pd.Categorical(merged["sale_date"].dt.day_name(), categories=weekdays, ordered=True)
    merged["month"] = merged["sale_date"].dt.month_name()

    pivot_weekday = pd.pivot_table(
        merged, index="category", columns="weekday", values="qty", aggfunc="sum", fill_value=0, observed=False
    )
    pivot_month = pd.pivot_table(
        merged, index="category", columns="month", values="qty", aggfunc="sum", fill_value=0, observed=False
    )
    return pivot_weekday, pivot_month

@timed
def stockouts(sales, min_rate=1.5, min_run=6):
    """Product-store pairs with >= min_rate receipts/day on average and a run of >= min_run zero-sale days."""
    # TODO: Product-store pairs with >= min_rate receipts/day on average and a run of >= min_run zero-sale days.
    df = sales.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    all_dates = pd.date_range(df["sale_date"].min(), df["sale_date"].max())
    n_days = len(all_dates)

    receipt_rates = df.groupby(["product_id", "store_id"])["receipt_id"].nunique() / n_days
    candidates = receipt_rates[receipt_rates >= min_rate].index

    daily_sales = df.groupby(["product_id", "store_id", "sale_date"])["qty"].sum()

    flagged = []
    for prod_id, store_id in candidates:
        sub = daily_sales.get((prod_id, store_id), pd.Series(dtype=float)).reindex(all_dates, fill_value=0)
        zeros = (sub == 0).astype(int)
        runs = zeros * (zeros.groupby((zeros != zeros.shift()).cumsum()).cumcount() + 1)
        if runs.max() >= min_run:
            flagged.append({
                "product_id": prod_id,
                "store_id": store_id,
                "rate": receipt_rates.loc[(prod_id, store_id)],
                "max_zero_run": runs.max()
            })

    return pd.DataFrame(flagged)

@timed
def store_productivity(sales, products, stores):
    """Revenue, margin, receipts and margin per sq ft per store."""
    # TODO: Revenue, margin, receipts and margin per sq ft per store.
    df = sales.copy()
    if "margin_ok" in df.columns:
        df = df[df["margin_ok"] != False]

    merged = df.merge(products, on="product_id", how="left", suffixes=("", "_prod"))
    disc = merged["discount_pct"] if "discount_pct" in merged.columns else 0.0
    net_price = merged["unit_price"] * (1.0 - disc / 100.0)

    merged["revenue"] = net_price * merged["qty"]
    merged["margin"] = (net_price - merged["cost_price"]) * merged["qty"]

    agg = merged.groupby("store_id", as_index=False).agg(
        revenue=("revenue", "sum"),
        margin=("margin", "sum"),
        receipts=("receipt_id", "nunique")
    )

    res = agg.merge(stores, on="store_id", how="left")
    res["margin_per_sq_ft"] = res["margin"] / res["floor_area_sqft"]
    return res