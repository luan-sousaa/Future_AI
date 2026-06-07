import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from google.adk.tools import ToolContext

EXCEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "repositories"
    / "historico_vendas_semanal_36m (2).xlsx"
)

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

# HELPERS
def load_excel_data() -> Optional[pd.DataFrame]:
    try:
        logger.info(f"Loading excel file from {EXCEL_PATH}")

        if not EXCEL_PATH.exists():
            logger.error(f"Excel file not found at {EXCEL_PATH}")
            return None

        df = pd.read_excel(
            EXCEL_PATH,
            sheet_name="Produtos",
            engine="openpyxl",
        )

        df = df.dropna(how="all")

        df = df.rename(
            columns={
                "CodProduto": "codigo_produto",
                "Descricao": "descricao_completa",
                "Familia": "familia_produto",
                "EAN": "codigo_ean_gtin",
                "Unidade": "unidade",
                "Inativo": "produto_inativo",
                "Preco": "preco_sintetico",
                "EstoqueAtual": "quantidade",
                "EstoqueMin": "estoque_minimo",
                "CoberturaMeses": "cobertura_meses",
                "Perfil": "perfil_venda",
                "StatusEstoque": "status_estoque",
                "VendaUlt13s": "venda_ult_13s",
                "VendaUlt52s": "venda_ult_52s",
                "MediaSemanal13": "media_semanal_13",
                "SemanasComVenda13": "semanas_com_venda_13",
            }
        )

        text_columns = [
            "codigo_produto",
            "descricao_completa",
            "familia_produto",
            "codigo_ean_gtin",
            "unidade",
            "produto_inativo",
            "perfil_venda",
            "status_estoque",
        ]

        for column in text_columns:
            df[column] = df[column].astype(str).str.strip()

        numeric_columns = [
            "preco_sintetico",
            "quantidade",
            "estoque_minimo",
            "cobertura_meses",
            "venda_ult_13s",
            "venda_ult_52s",
            "media_semanal_13",
            "semanas_com_venda_13",
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        logger.info(f"Excel loaded successfully with {len(df)} rows.")
        return df

    except Exception:
        logger.exception("Failed to load Excel file.")
        return None

def _get_product_by_code(product_code: str) -> Optional[dict]:
    try:
        logger.info(f"Fetching product by code: {product_code}")

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
        logger.exception("Failed to fetch product by code.")
        return None

# Tools agente
def search_product_by_name(
    term: str,
    limit: int = 10,
    tool_context: Optional[ToolContext] = None,
) -> list:
    """
    Return matching products by name or description for product discovery.
    """
    try:
        logger.info("Searching for products with term: %s", term)

        if not term or not term.strip():
            logger.warning("Empty search term")
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
        ].head(limit)

        records = resultados.to_dict(orient="records")

        if tool_context is not None:
            tool_context.state["last_search_term"] = term
            tool_context.state["last_search_results"] = records

        logger.info("Found %d matching products", len(records))
        return records
    except Exception:
        logger.exception("Failed to search products by name.")
        return []

def get_product_by_code(
    product_code: str,
    tool_context: Optional[ToolContext] = None,
) -> Optional[dict]:
    """
    Return one product record by its exact internal product code.
    """
    try:
        logger.info("Getting product by code: %s", product_code)

        produto = _get_product_by_code(product_code)
        if produto is None:
            return None

        if tool_context is not None:
            selected_codes = tool_context.state.get("selected_product_codes", [])
            selected_products = tool_context.state.get("selected_products", [])

            if produto["codigo_produto"] not in selected_codes:
                selected_codes.append(produto["codigo_produto"])
                selected_products.append(produto)

            tool_context.state["selected_product_codes"] = selected_codes
            tool_context.state["selected_products"] = selected_products

        return produto

    except Exception:
        logger.exception("Failed to select product by code")
        return None

def get_product_stock_and_price_summary(
    product_code: str,
    tool_context: Optional[ToolContext] = None,
) -> Optional[dict]:
    """
    Return a compact stock and pricing summary for one product code.
    """
    try:
        logger.info("Building stock and price summary for code: %s", product_code)

        produto = _get_product_by_code(product_code)
        if produto is None:
            logger.warning("Product code %s not found for summary", product_code)
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

        if tool_context is not None:
            tool_context.state["last_product_summary"] = resumo

        return resumo

    except Exception:
        logger.exception("Failed to get stock and price summary for code: %s", product_code)
        return None


# Controle de Estoque
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
