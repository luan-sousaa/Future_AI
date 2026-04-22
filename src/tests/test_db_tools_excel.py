from pathlib import Path
import sys
import logging
from pprint import pprint

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.tools.db_tools_excel import (
    load_excel_data,
    search_product_by_name,
    get_product_by_code,
    get_product_stock_and_price_summary,
    get_low_stock_products,
    get_inactive_products,
)


def run_manual_tests() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s"
    )

    print("\n=== TESTE 1: LOAD EXCEL DATA ===")
    df = load_excel_data()
    if df is not None:
        print(df.head())
    else:
        print("Falha ao carregar o Excel.")

    print("\n=== TESTE 2: SEARCH PRODUCT BY NAME ===")
    pprint(search_product_by_name("churrasqueira"))

    print("\n=== TESTE 3: GET PRODUCT BY CODE ===")
    pprint(get_product_by_code("00021"))

    print("\n=== TESTE 4: STOCK AND PRICE SUMMARY ===")
    pprint(get_product_stock_and_price_summary("00021"))

    print("\n=== TESTE 5: LOW STOCK PRODUCTS ===")
    pprint(get_low_stock_products(limit=5))

    print("\n=== TESTE 6: INACTIVE PRODUCTS ===")
    pprint(get_inactive_products(limit=5))


if __name__ == "__main__":
    run_manual_tests()
