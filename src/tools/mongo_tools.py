import logging
from datetime import datetime
from typing import Any

from google.adk.tools import ToolContext

from src.config.alerts.alert_enums import AlertTypeEnum

from src.services.inventory.inventory_types import InventoryOverviewResponse

logger = logging.getLogger(__name__)

_inventory_service = None


def _get_inventory_service():
    global _inventory_service

    if _inventory_service is None:
        logger.debug("Initializing InventoryService (first call)")
        from src.services.inventory.inventory_service import InventoryService

        _inventory_service = InventoryService()
        logger.debug("InventoryService initialized successfully")

    return _inventory_service

def _resolve_product_code(
    tool_context: ToolContext,
    explicit_code: str = "",
) -> str:
    """Resolve a single product code from the explicit argument or session state.

    Resolution order: explicit argument → selected_product → selected_product_last
    → last_search_product_codes (only when it holds exactly one result).
    Returns an empty string when no code can be resolved.
    """
    if explicit_code:
        return explicit_code

    selected_product = tool_context.state.get("selected_product", {})
    code = selected_product.get("codigo_produto", "")
    if code:
        logger.debug("Resolved product code from selected_product | %r", code)
        return code

    code = tool_context.state.get("selected_product_last", "")
    if code:
        logger.debug("Resolved product code from selected_product_last | %r", code)
        return code

    last_search_codes = tool_context.state.get("last_search_product_codes", [])
    if len(last_search_codes) == 1:
        logger.debug(
            "Resolved product code from last_search_product_codes | %r",
            last_search_codes[0],
        )
        return last_search_codes[0]

    return ""


def _compact_product(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "codigo_produto": product.get("codigo_produto"),
        "descricao_completa": product.get("descricao_completa"),
        "familia_produto": product.get("familia_produto"),
        "unidade": product.get("unidade"),
        "preco_sintetico": product.get("preco_sintetico"),
        "quantidade": product.get("quantidade"),
        "estoque_minimo": product.get("estoque_minimo"),
        "status_estoque": product.get("status_estoque"),
        "perfil_venda": product.get("perfil_venda"),
        "venda_ult_13s": product.get("venda_ult_13s"),
        "media_semanal_13": product.get("media_semanal_13"),
        "cobertura_meses": product.get("cobertura_meses"),
    }

def search_product_by_name(
    tool_context: ToolContext,
    term: str,
    limit: int = 10,
    skip: int = 0,
) -> list[dict[str, Any]]:

    logger.info(
        "Searching products by name | "
        f"term={term!r} | limit={limit} | skip={skip}"
    )

    try:
        if not term.strip():
            logger.warning("Empty search term provided — returning empty list")
            return []

        products = (
            _get_inventory_service().search_products_by_name(
                term=term,
                limit=limit,
                skip=skip,
            )
        )

        logger.info(
            f"Search returned {len(products)} product(s) for term={term!r}"
        )

        tool_context.state["last_search_term"] = term

        tool_context.state["last_search_product_codes"] = [
            product["codigo_produto"]
            for product in products
        ]

        search_results = [
            _compact_product(product)
            for product in products
        ]

        tool_context.state["last_search_products"] = search_results

        if len(search_results) == 1:
            selected_product = search_results[0]
            selected_code = selected_product["codigo_produto"]

            logger.info(
                "Single result found — auto-selecting product | "
                f"codigo_produto={selected_code!r}"
            )

            tool_context.state["selected_product"] = selected_product
            tool_context.state["selected_product_last"] = selected_code
            tool_context.state["selected_product_codes"] = [selected_code]

        return search_results

    except Exception:
        logger.exception(
            f"Failed to search products | term={term!r}"
        )
        return []


def get_product_by_code(
    tool_context: ToolContext,
    product_code: str,
) -> dict[str, Any] | None:

    logger.info(f"Fetching product by code | codigo_produto={product_code!r}")

    try:
        product = (
            _get_inventory_service().get_product_by_code(product_code)
        )

        if not product:
            logger.warning(
                f"Product not found | codigo_produto={product_code!r}"
            )
            return None

        logger.info(
            f"Product found | codigo_produto={product_code!r} | "
            f"descricao={product.get('descricao_completa')!r}"
        )

        selected_codes = tool_context.state.get("selected_product_codes", [])

        if product_code not in selected_codes:
            selected_codes.append(product_code)
            logger.debug(
                f"Added {product_code!r} to selected_product_codes | "
                f"total={len(selected_codes)}"
            )

        tool_context.state["selected_product_codes"] = selected_codes
        tool_context.state["selected_product_last"] = product_code
        tool_context.state["selected_product"] = {
            "codigo_produto": product["codigo_produto"],
            "descricao_completa": product["descricao_completa"],
            "familia_produto": product.get("familia_produto"),
            "unidade": product.get("unidade"),
            "quantidade": product.get("quantidade"),
            "estoque_minimo": product.get("estoque_minimo"),
            "preco_sintetico": product.get("preco_sintetico"),
        }

        return {
            "codigo_produto": product["codigo_produto"],
            "descricao_completa": product["descricao_completa"],
            "familia_produto": product.get("familia_produto"),
            "unidade": product.get("unidade"),
        }

    except Exception:
        logger.exception(
            f"Failed to get product | codigo_produto={product_code!r}"
        )
        return None


def get_product_stock_and_price_summary(
    tool_context: ToolContext,
) -> list[dict[str, Any]]:
    
    logger.info("Building stock and price summary")

    try:
        selected_codes = tool_context.state.get("selected_product_codes", [])

        selected_product = tool_context.state.get("selected_product", {})

        if not selected_codes and selected_product.get("codigo_produto"):
            selected_codes = [selected_product["codigo_produto"]]
            logger.debug(
                "No selected_codes in state — falling back to selected_product | "
                f"codigo_produto={selected_codes[0]!r}"
            )

        if not selected_codes:
            last_stock_check = tool_context.state.get("last_stock_check", {})
            if last_stock_check.get("codigo_produto"):
                selected_codes = [last_stock_check["codigo_produto"]]
                logger.debug(
                    "Falling back to last_stock_check | "
                    f"codigo_produto={selected_codes[0]!r}"
                )

        if not selected_codes:
            last_search_codes = tool_context.state.get(
                "last_search_product_codes", []
            )
            if len(last_search_codes) == 1:
                selected_codes = last_search_codes
                logger.debug(
                    "Falling back to last_search_product_codes (single result) | "
                    f"codigo_produto={selected_codes[0]!r}"
                )

        if not selected_codes:
            logger.warning(
                "No product codes available to build summary — returning empty list"
            )
            return []

        logger.info(
            f"Fetching summary for {len(selected_codes)} product code(s) | "
            f"codes={selected_codes}"
        )

        products = (
            _get_inventory_service().get_products_by_codes(selected_codes)
        )

        logger.info(
            f"Summary built for {len(products)} product(s)"
        )

        return [
            {
                "codigo_produto": p["codigo_produto"],
                "descricao_completa": p["descricao_completa"],
                "familia_produto": p.get("familia_produto"),
                "unidade": p.get("unidade"),
                "quantidade": p.get("quantidade"),
                "estoque_minimo": p.get("estoque_minimo"),
                "preco_sintetico": p.get("preco_sintetico"),
            }
            for p in products
        ]

    except Exception:
        logger.exception("Failed to build stock and price summary")
        return []


def check_product_availability(
    tool_context: ToolContext,
    product_code: str,
    requested_quantity: int,
) -> dict[str, Any]:

    logger.info(
        "Checking product availability | "
        f"codigo_produto={product_code!r} | "
        f"requested_quantity={requested_quantity}"
    )

    try:
        product_code = _resolve_product_code(tool_context, product_code)

        if not product_code:
            logger.warning(
                "Could not resolve any product code for availability check"
            )
            return {
                "disponivel": False,
                "message": "No product selected.",
            }

        result = (
            _get_inventory_service().validate_stock_availability(
                product_code,
                requested_quantity,
            )
        )

        logger.info(
            f"Availability result | codigo_produto={product_code!r} | "
            f"requested={requested_quantity} | "
            f"disponivel={result.get('disponivel')}"
        )

        selected_product = tool_context.state.get("selected_product", {})
        if selected_product.get("descricao_completa"):
            result["descricao_completa"] = selected_product["descricao_completa"]

        tool_context.state["last_stock_check"] = result

        return result

    except ValueError as exc:
        logger.warning(
            f"Validation error on availability check | "
            f"codigo_produto={product_code!r} | error={exc}"
        )
        return {
            "disponivel": False,
            "message": str(exc),
        }

    except Exception:
        logger.exception(
            f"Failed to validate stock | codigo_produto={product_code!r}"
        )
        return {
            "disponivel": False,
            "message": "Failed to validate stock.",
        }


def get_inventory_overview() -> InventoryOverviewResponse:

    logger.info("Fetching inventory overview")

    try:
        result = _get_inventory_service().get_inventory_overview()

        summary = result.get("summary", {})
        logger.info(
            "Inventory overview fetched | "
            f"total={summary.get('total_produtos')} | "
            f"abaixo_minimo={summary.get('abaixo_estoque_minimo')} | "
            f"sem_estoque={summary.get('sem_estoque')} | "
            f"negativo={summary.get('estoque_negativo')} | "
            f"inativos={summary.get('inativos')} | "
            f"status={result.get('status')!r}"
        )

        return result

    except Exception:
        logger.exception("Failed to get inventory overview")
        return {
            "summary": {
                "total_produtos": 0,
                "abaixo_estoque_minimo": 0,
                "sem_estoque": 0,
                "estoque_negativo": 0,
                "inativos": 0,
            },
            "status": "unknown",
        }


def get_critical_stock_products(
    alert_type: AlertTypeEnum,
    limit: int = 20,
) -> list[dict]:

    logger.info(
        f"Fetching critical stock products | alert_type={alert_type!r} | limit={limit}"
    )

    try:
        result = _get_inventory_service().get_critical_stock_products(
            alert_type=alert_type,
            limit=limit,
        )

        logger.info(
            f"Critical stock products fetched | "
            f"alert_type={alert_type!r} | count={len(result)}"
        )

        return result

    except Exception:
        logger.exception(
            f"Failed to get critical stock products | alert_type={alert_type!r}"
        )
        return []


def get_inactive_products(
    limit: int = 20,
) -> list[dict]:

    logger.info(f"Fetching inactive products | limit={limit}")

    try:
        result = _get_inventory_service().get_inactive_products(limit=limit)

        logger.info(f"Inactive products fetched | count={len(result)}")

        return result

    except Exception:
        logger.exception("Failed to get inactive products")
        return []


def get_inventory_diff_by_period(
    reference_period: str,
    reference_date: str = "",
    limit: int = 20,
) -> list[dict]:

    if not reference_date:
        reference_date = datetime.now().date().isoformat()
        logger.debug(
            f"No reference_date provided — defaulting to today | {reference_date}"
        )

    logger.info(
        "Fetching inventory diff by period | "
        f"reference_date={reference_date} | "
        f"reference_period={reference_period!r} | "
        f"limit={limit}"
    )

    try:
        result = _get_inventory_service().get_inventory_diff_by_period(
            reference_date=reference_date,
            reference_period=reference_period,
            limit=limit,
        )

        logger.info(
            f"Inventory diff fetched | "
            f"reference_period={reference_period!r} | "
            f"count={len(result)}"
        )

        return result

    except Exception:
        logger.exception(
            "Failed to get inventory diff by period | "
            f"reference_date={reference_date} | "
            f"reference_period={reference_period!r}"
        )
        return []
    
def get_product_commercial_context(
    tool_context: ToolContext,
    product_code: str = "",
) -> dict[str, Any] | None:
    try:
        product_code = _resolve_product_code(tool_context, product_code)

        if not product_code:
            return None

        result = (
            _get_inventory_service()
            .get_product_commercial_context(product_code)
        )

        if result:
            tool_context.state["selected_product"] = result
            tool_context.state["selected_product_last"] = result["codigo_produto"]
            tool_context.state["selected_product_codes"] = [result["codigo_produto"]]

        return result

    except Exception:
        logger.exception("Failed to get product commercial context")
        return None

def get_products_by_stock_status(
    status_estoque: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    try:
        products = (
            _get_inventory_service()
            .get_products_by_stock_status(
                status_estoque=status_estoque,
                limit=limit,
            )
        )

        return [
            _compact_product(product)
            for product in products
        ]

    except Exception:
        logger.exception("Failed to get products by stock status")
        return []
    
def get_top_selling_products(
    period: str = "13w",
    limit: int = 20,
) -> list[dict[str, Any]]:
    try:
        products = (
            _get_inventory_service()
            .get_top_selling_products(
                period=period,
                limit=limit,
            )
        )

        return [
            _compact_product(product)
            for product in products
        ]

    except Exception:
        logger.exception("Failed to get top selling products")
        return []
    
def get_slow_moving_products(
    limit: int = 20,
) -> list[dict[str, Any]]:
    try:
        products = (
            _get_inventory_service()
            .get_slow_moving_products(limit=limit)
        )

        return [
            _compact_product(product)
            for product in products
        ]

    except Exception:
        logger.exception("Failed to get slow moving products")
        return []
    
def get_overstocked_products(
    limit: int = 20,
) -> list[dict[str, Any]]:
    try:
        products = (
            _get_inventory_service()
            .get_overstocked_products(limit=limit)
        )

        return [
            _compact_product(product)
            for product in products
        ]

    except Exception:
        logger.exception("Failed to get overstocked products")
        return []