import sys
import os
import csv
from datetime import datetime

# Add project root to Python path
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
)

from config import Config
from database.connection import init_db_pool, execute_update


def parse_date(date_str):
    """
    Convert CSV date into MySQL-compatible YYYY-MM-DD format.
    Supports common formats used in the Global Sales dataset.
    """
    formats = [
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y-%m-%d',
        '%m-%d-%Y',
        '%d-%m-%Y'
    ]

    date_str = date_str.strip()

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Unknown date format: {date_str}")


def clean_number(value):
    """
    Converts numbers such as:
    1234.56
    1,234.56
    6.69E+08
    into numeric values.
    """
    if value is None:
        return 0

    value = str(value).strip()
    value = value.replace(',', '')
    value = value.replace('$', '')

    return float(value)


def import_global_sales(filepath):

    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return False

    print(f"Starting import from: {filepath}")

    success_count = 0
    row_count = 0

    try:
        with open(
            filepath,
            mode='r',
            encoding='utf-8-sig',
            newline=''
        ) as file:

            reader = csv.DictReader(file)

            if not reader.fieldnames:
                print("ERROR: CSV has no headers.")
                return False

            print("\nDetected columns:")
            print(", ".join(reader.fieldnames))
            print()

            # Required columns from Global Sales dataset
            required_columns = [
                'Region',
                'Country',
                'Item Type',
                'Sales Channel',
                'Order Priority',
                'Order Date',
                'Order ID',
                'Ship Date',
                'Units Sold',
                'Unit Price',
                'Unit Cost',
                'Total Revenue',
                'Total Cost',
                'Total Profit'
            ]

            missing = [
                col for col in required_columns
                if col not in reader.fieldnames
            ]

            if missing:
                print("ERROR: Missing columns:")
                print(missing)
                return False

            for row in reader:

                row_count += 1

                try:
                    region = row['Region'].strip()
                    country = row['Country'].strip()
                    item_type = row['Item Type'].strip()
                    sales_channel = row['Sales Channel'].strip()
                    order_priority = row['Order Priority'].strip()

                    order_date = parse_date(
                        row['Order Date']
                    )

                    ship_date = parse_date(
                        row['Ship Date']
                    )

                    # Convert scientific notation correctly
                    order_id = int(
                        clean_number(row['Order ID'])
                    )

                    units_sold = int(
                        clean_number(row['Units Sold'])
                    )

                    unit_price = clean_number(
                        row['Unit Price']
                    )

                    unit_cost = clean_number(
                        row['Unit Cost']
                    )

                    total_revenue = clean_number(
                        row['Total Revenue']
                    )

                    total_cost = clean_number(
                        row['Total Cost']
                    )

                    total_profit = clean_number(
                        row['Total Profit']
                    )

                    query = """
                        INSERT INTO global_sales (
                            region,
                            country,
                            item_type,
                            sales_channel,
                            order_priority,
                            order_date,
                            order_id,
                            ship_date,
                            units_sold,
                            unit_price,
                            unit_cost,
                            total_revenue,
                            total_cost,
                            total_profit
                        )
                        VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
                    """

                    execute_update(
                        query,
                        (
                            region,
                            country,
                            item_type,
                            sales_channel,
                            order_priority,
                            order_date,
                            order_id,
                            ship_date,
                            units_sold,
                            unit_price,
                            unit_cost,
                            total_revenue,
                            total_cost,
                            total_profit
                        )
                    )

                    success_count += 1

                except Exception as row_error:

                    print(
                        f"Skipping row {row_count}: "
                        f"{row_error}"
                    )

            print("\n----------------------------------------")
            print("IMPORT COMPLETED")
            print("----------------------------------------")
            print(
                f"Successfully imported: "
                f"{success_count} / {row_count}"
            )

            return success_count > 0

    except Exception as error:

        print(f"ERROR reading CSV: {error}")
        return False


def main():

    if len(sys.argv) < 2:

        print(
            "Usage:\n"
            "python database/import_dataset.py "
            "<csv_file>"
        )

        sys.exit(1)

    csv_path = sys.argv[1]

    try:

        print("Initializing database connection...")

        init_db_pool(Config)

        import_global_sales(csv_path)

    except Exception as error:

        print(
            f"Import execution failed: {error}"
        )

        sys.exit(1)


if __name__ == '__main__':
    main()