"""CLI:  python -m freshmart report --store 3 --month 6"""
import argparse
import pandas as pd
from .loader import SalesLoader
from .cleaner import clean_sales, clean_products, QualityLog
from .report import top_margin, store_productivity, stockouts

def main():
    ap = argparse.ArgumentParser(prog="freshmart")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report"); r.add_argument("--data", default="data"); r.add_argument("--store", type=int); r.add_argument("--month", type=int)
    args = ap.parse_args()
    # TODO: load -> clean -> filter by month if given -> print top_margin, store_productivity, stockouts
    log = QualityLog()
    loader = SalesLoader(args.data)
    d = loader.load_all()

    # Clean products and sales
    products_clean = clean_products(d["products"], log)
    sales_clean = clean_sales(d["sales"], products_clean, d["stores"], log)

    # Filter by month if given
    if args.month is not None:
        sales_clean = sales_clean[sales_clean["sale_date"].dt.month == args.month]

    print("=== Top Margin Products ===")
    print(top_margin(sales_clean, products_clean, store_id=args.store))

    print("\n=== Store Productivity ===")
    print(store_productivity(sales_clean, products_clean, d["stores"]))

    print("\n=== Potential Stockouts ===")
    print(stockouts(sales_clean))

if __name__ == "__main__":
    main()