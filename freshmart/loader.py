"""Load and validate the four FreshMart files."""
from pathlib import Path
import pandas as pd

REQUIRED = {
    "sales_2025.csv": ["receipt_id", "store_id", "product_id", "sale_date", "qty", "unit_price", "discount_pct"],
    "products.csv": ["product_id", "product_name", "category", "unit_price", "cost_price", "is_perishable"],
    "stores.csv": ["store_id", "store_name", "city", "opened_on", "floor_area_sqft"],
    "promotions.csv": ["promo_id", "product_id", "store_id", "start_date", "end_date", "discount_pct"],
}

class DataFileError(Exception):
    """A required file is missing or unreadable."""

class SchemaError(Exception):
    """A file is missing required columns."""

class SalesLoader:
    """Reads the four CSVs from a folder and validates their columns."""
    def __init__(self, folder):
        self.folder = Path(folder)
        # TODO: raise DataFileError if the folder does not exist
        if not self.folder.exists() or not self.folder.is_dir():
            raise DataFileError(f"Directory not found: {self.folder}")

    def _read(self, name):
        # TODO: raise DataFileError if the file is missing
        file_path = self.folder / name
        if not file_path.is_file():
            raise DataFileError(f"Required file is missing: {file_path}")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise DataFileError(f"Could not read file {file_path}: {e}")

        # TODO: raise SchemaError listing any missing REQUIRED columns
        required_cols = REQUIRED.get(name, [])
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise SchemaError(f"File '{name}' is missing required columns: {missing_cols}")

        return df

    def load_all(self):
        return {name.split(".")[0].replace("_2025", ""): self._read(name) for name in REQUIRED}

    def stream_sales(self, chunksize=5000):
        """Generator: yield the sales file chunk by chunk (pd.read_csv(..., chunksize=))."""
        # TODO
        file_path = self.folder / "sales_2025.csv"
        if not file_path.is_file():
            raise DataFileError(f"Sales file missing: {file_path}")

        # Validate schema on first chunk before streaming
        first_chunk = pd.read_csv(file_path, nrows=5)
        required_cols = REQUIRED.get("sales_2025.csv", [])
        missing_cols = [col for col in required_cols if col not in first_chunk.columns]
        if missing_cols:
            raise SchemaError(f"File 'sales_2025.csv' is missing required columns: {missing_cols}")

        yield from pd.read_csv(file_path, chunksize=chunksize)