# FreshMart Retail Chain: Sales Intelligence Pipeline

A modular data processing and business intelligence pipeline developed in Python for a retail chain across 5 supermarkets. The system automates data ingestion, schema validation, audit logging, hypothesis testing, and store performance reporting.

---

## Architecture & Features

- **Robust Ingestion (`loader.py`)**: Validates input data integrity using custom exceptions (`DataFileError`, `SchemaError`) and provides a generator (`stream_sales()`) for memory-efficient chunk processing.
- **Audited Data Cleaning (`cleaner.py`)**: Sanitizes sales and catalog datasets while recording all modifications, fixes, and business rules inside an audit-ready `QualityLog`.
- **Analytical Intelligence (`report.py`)**:
  - **Top Margin Drivers**: Identifies highest net-profit products per store location.
  - **Promotion Lift & Permutation Testing**: Assesses promotional campaign validity via statistical significance tests ($p < 0.05$).
  - **Category Seasonality**: Generates monthly and day-of-week sales heatmaps.
  - **Stock-Out Detection**: Identifies abnormal zero-sale runs on high-velocity items and estimates unrealized revenue loss.
  - **Floor Space Productivity**: Evaluates margin per square foot to rank physical retail performance.
- **Command-Line Interface (`main.py`)**: Generates automated management reports directly from the terminal.

---

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/nabiha-ds/freshmart-sales-intelligence.git](https://github.com/nabiha-ds/freshmart-sales-intelligence.git)
   cd freshmart-sales-intelligence