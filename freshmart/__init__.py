"""FreshMart sales intelligence package."""
from .loader import SalesLoader, DataFileError, SchemaError
from .cleaner import clean_sales, clean_products, QualityLog
from .report import top_margin, promo_lift, patterns, stockouts, store_productivity, timed