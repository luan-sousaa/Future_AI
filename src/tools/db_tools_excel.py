from typing import Optional

import pandas as pd
from pathlib import Path
import logging

EXCEL_PATH = Path(__file__).resolve().parent.parent / "repositories" / "pivot-5_com_precos.xlsx"

logger = logging.getLogger(__name__)

COLUNAS = [
    "descricao_completa",
    "familia_produto",
    "codigo_produto",
    "codigo_ean_gtin",
    "produto_inativo",
    "unidade",
    "quantidade",
    "estoque_minimo",
    "preco_sintetico",
]

def load_excel_data() -> Optional[pd.DataFrame]:
    """
    Load and normalize the Excel inventory table for reuse by the other tools.
    """
    try:
        logger.info(f"Loading excel file from {EXCEL_PATH}")

        if not EXCEL_PATH.exists():
            logger.error(f"Excel file not found at {EXCEL_PATH}")
            return None

        df = pd.read_excel(
            EXCEL_PATH,
            sheet_name="Sheet1",
            skiprows=4,
            header=None,
            names=COLUNAS,
            engine="openpyxl",
        )

        df = df.dropna(how="all")

        df["descricao_completa"] = df["descricao_completa"].astype(str).str.strip()
        df["familia_produto"] = df["familia_produto"].astype(str).str.strip()
        df["codigo_produto"] = df["codigo_produto"].astype(str).str.strip()
        df["codigo_ean_gtin"] = df["codigo_ean_gtin"].astype(str).str.strip()
        df["produto_inativo"] = df["produto_inativo"].astype(str).str.strip()
        df["unidade"] = df["unidade"].astype(str).str.strip()

        df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
        df["estoque_minimo"] = pd.to_numeric(df["estoque_minimo"], errors="coerce")
        df["preco_sintetico"] = pd.to_numeric(df["preco_sintetico"], errors="coerce")

        logger.info(f"Excel loaded successfully with {len(df)} rows.")
        return df

    except Exception:
        logger.exception("Failed to load Excel file.")
        return None

def search_product_by_name(term: str, limit: int = 10) -> list:
    """
    Return matching products by name or description for product discovery.
    """
    try:
        logger.info(f"Searching for products with term: {term}")

        if not term or not term.strip():
            logger.warning("Empty seach term")
            return []

        df = load_excel_data()
        if df is None:
            return []

        filtro = df["descricao_completa"].str.lower().str.contains(term.lower(), na=False)

        resultados = df.loc[
            filtro,
            [
                "codigo_produto",
                "descricao_completa",
                "familia_produto",
                "unidade",
                "preco_sintetico",
            ],
        ]

        records = resultados.head(limit).to_dict(orient="records")
        logger.info(f"Found {len(records)} matching products")
        return records
    except Exception:
        logger.exception("Failed to search products by name.")
        return []

def get_product_by_code(product_code: str) -> Optional[dict]:
    """
    Return one product record by its exact internal product code.
    """
    try:
        logger.info(f"Getting product by code: {product_code}")

        if not product_code or not product_code.strip():
            logger.warning("Empty product code")
            return None

        df = load_excel_data()
        if df is None:
            return None

        resultado = df[df["codigo_produto"] == product_code].copy()

        if resultado.empty:
            logger.warning(f"No product found with code: {product_code}")
            return None

        row = resultado.iloc[0]

        produto = {
            "codigo_produto": row["codigo_produto"],
            "descricao_completa": row["descricao_completa"],
            "familia_produto": row["familia_produto"],
            "codigo_ean_gtin": row["codigo_ean_gtin"],
            "produto_inativo": row["produto_inativo"],
            "unidade": row["unidade"],
            "quantidade": None if pd.isna(row["quantidade"]) else float(row["quantidade"]),
            "estoque_minimo": None if pd.isna(row["estoque_minimo"]) else float(row["estoque_minimo"]),
            "preco_sintetico": None if pd.isna(row["preco_sintetico"]) else float(row["preco_sintetico"]),
        }

        logger.info(f"Product found: {produto['descricao_completa']}")
        return produto

    except Exception:
        logger.exception("Failed to get product by code")
        return None

def get_product_stock_and_price_summary(product_code: str) -> Optional[dict]:
    """
    Return a compact stock and pricing summary for one product code.
    """
    try:
        logger.info(f"Building stock and price summary for code: {product_code}")

        produto = get_product_by_code(product_code)
        if produto is None:
            logger.warning(f"Cannot build summary, product not found for code: {product_code}")
            return None

        resumo = {
            "codigo_produto": produto["codigo_produto"],
            "descricao_completa": produto["descricao_completa"],
            "familia_produto": produto["familia_produto"],
            "unidade": produto["unidade"],
            "produto_inativo": produto["produto_inativo"],
            "quantidade_em_estoque": produto["quantidade"],
            "estoque_minimo": produto["estoque_minimo"],
            "preco_sintetico": produto["preco_sintetico"],
        }

        logger.info(f"Summary created for product code: {product_code}")
        return resumo

    except Exception:
        logger.exception(f"Failed to get stock and price summary for product code: {product_code}")
        return None


def get_low_stock_products(limit: int = 20) -> list:
    """Return products whose current stock is below the configured minimum stock."""
    try:
        logger.info("Searching for products below minimum stock")

        df = load_excel_data()
        if df is None:
            return []

        filtrado = df[
            (df["quantidade"].notna()) &
            (df["estoque_minimo"].notna()) &
            (df["quantidade"] < df["estoque_minimo"])
            ]

        resultados = filtrado[
            [
                "codigo_produto",
                "descricao_completa",
                "quantidade",
                "estoque_minimo",
                "preco_sintetico",
            ]
        ].head(limit)

        records = resultados.to_dict(orient="records")
        logger.info(f"Found {len(records)} products below minimum stock")
        return records

    except Exception:
        logger.exception("Failed to get low stock products.")
        return []

def get_inactive_products(limit: int = 20) -> list:
    """
    Return inactive products to support catalog cleanup or stock review.
    """
    try:
        logger.info("Searching for inactive products")

        df = load_excel_data()
        if df is None:
            return []

        filtrado = df[df["produto_inativo"].str.lower() == "sim"]

        resultados = filtrado[
            [
                "codigo_produto",
                "descricao_completa",
                "familia_produto",
                "unidade",
                "preco_sintetico",
            ]
        ].head(limit)

        records = resultados.to_dict(orient="records")
        logger.info(f"Found {len(records)} inactive products")
        return records

    except Exception:
        logger.exception("Failed to get inactive products.")
        return []
