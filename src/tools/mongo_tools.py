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
        from src.services.inventory.inventory_service import InventoryService

        _inventory_service = InventoryService()

    return _inventory_service

def search_product_by_name(
    tool_context: ToolContext,
    term: str,
    limit: int = 10,
    skip: int = 0,
) -> list[dict[str, Any]]:

    try:
        if not term.strip():
            return []

        products = (
            _get_inventory_service().search_products_by_name(
                term=term,
                limit=limit,
                skip=skip,
            )
        )

        tool_context.state[
            "last_search_term"
        ] = term

        tool_context.state[
            "last_search_product_codes"
        ] = [
            product["codigo_produto"]
            for product in products
        ]

        search_results = [
            {
                "codigo_produto": p[
                    "codigo_produto"
                ],
                "descricao_completa": p[
                    "descricao_completa"
                ],
                "familia_produto": p.get(
                    "familia_produto"
                ),
                "unidade": p.get("unidade"),
                "preco_sintetico": p.get(
                    "preco_sintetico"
                ),
            }
            for p in products
        ]

        tool_context.state[
            "last_search_products"
        ] = search_results

        if len(search_results) == 1:
            selected_product = search_results[0]
            selected_code = selected_product[
                "codigo_produto"
            ]

            tool_context.state[
                "selected_product"
            ] = selected_product

            tool_context.state[
                "selected_product_last"
            ] = selected_code

            tool_context.state[
                "selected_product_codes"
            ] = [selected_code]

        return search_results

    except Exception:
        logger.exception(
            "Failed to search products"
        )
        return []


def get_product_by_code(
    tool_context: ToolContext,
    product_code: str,
) -> dict[str, Any] | None:

    try:
        product = (
            _get_inventory_service().get_product_by_code(
                product_code
            )
        )

        if not product:
            return None

        selected_codes = tool_context.state.get(
            "selected_product_codes",
            [],
        )

        product_code = product[
            "codigo_produto"
        ]

        if (
            product_code
            not in selected_codes
        ):
            selected_codes.append(
                product_code
            )

        tool_context.state[
            "selected_product_codes"
        ] = selected_codes

        tool_context.state[
            "selected_product_last"
        ] = product_code

        tool_context.state[
            "selected_product"
        ] = {
            "codigo_produto": product[
                "codigo_produto"
            ],
            "descricao_completa": product[
                "descricao_completa"
            ],
            "familia_produto": product.get(
                "familia_produto"
            ),
            "unidade": product.get(
                "unidade"
            ),
            "quantidade": product.get(
                "quantidade"
            ),
            "estoque_minimo": product.get(
                "estoque_minimo"
            ),
            "preco_sintetico": product.get(
                "preco_sintetico"
            ),
        }

        return {
            "codigo_produto": product[
                "codigo_produto"
            ],
            "descricao_completa": product[
                "descricao_completa"
            ],
            "familia_produto": product.get(
                "familia_produto"
            ),
            "unidade": product.get(
                "unidade"
            ),
        }

    except Exception:
        logger.exception(
            "Failed to get product"
        )
        return None


def get_product_stock_and_price_summary(
    tool_context: ToolContext,
) -> list[dict[str, Any]]:

    try:
        selected_codes = tool_context.state.get(
            "selected_product_codes",
            [],
        )

        selected_product = tool_context.state.get(
            "selected_product",
            {},
        )

        if (
            not selected_codes
            and selected_product.get("codigo_produto")
        ):
            selected_codes = [
                selected_product["codigo_produto"]
            ]

        if not selected_codes:
            last_stock_check = tool_context.state.get(
                "last_stock_check",
                {},
            )
            if last_stock_check.get("codigo_produto"):
                selected_codes = [
                    last_stock_check["codigo_produto"]
                ]

        if not selected_codes:
            last_search_codes = tool_context.state.get(
                "last_search_product_codes",
                [],
            )
            if len(last_search_codes) == 1:
                selected_codes = last_search_codes

        if not selected_codes:
            return []

        products = (
            _get_inventory_service().get_products_by_codes(
                selected_codes
            )
        )

        return [
            {
                "codigo_produto": p[
                    "codigo_produto"
                ],
                "descricao_completa": p[
                    "descricao_completa"
                ],
                "familia_produto": p.get(
                    "familia_produto"
                ),
                "unidade": p.get("unidade"),
                "quantidade": p.get(
                    "quantidade"
                ),
                "estoque_minimo": p.get(
                    "estoque_minimo"
                ),
                "preco_sintetico": p.get(
                    "preco_sintetico"
                ),
            }
            for p in products
        ]

    except Exception:
        logger.exception(
            "Failed to build summary"
        )
        return []


def check_product_availability(
    tool_context: ToolContext,
    product_code: str,
    requested_quantity: int,
) -> dict[str, Any]:

    try:
        if not product_code:
            selected_product = tool_context.state.get(
                "selected_product",
                {},
            )
            product_code = selected_product.get(
                "codigo_produto",
                "",
            )

        if not product_code:
            product_code = tool_context.state.get(
                "selected_product_last",
                "",
            )

        if not product_code:
            last_search_codes = tool_context.state.get(
                "last_search_product_codes",
                [],
            )
            if len(last_search_codes) == 1:
                product_code = last_search_codes[0]

        if not product_code:
            return {
                "disponivel": False,
                "message": (
                    "No product selected."
                ),
            }

        result = (
            _get_inventory_service().validate_stock_availability(
                product_code,
                requested_quantity,
            )
        )

        selected_product = tool_context.state.get(
            "selected_product",
            {},
        )

        if selected_product.get("descricao_completa"):
            result["descricao_completa"] = (
                selected_product["descricao_completa"]
            )

        tool_context.state[
            "last_stock_check"
        ] = result

        return result

    except ValueError as exc:
        return {
            "disponivel": False,
            "message": str(exc),
        }

    except Exception:
        logger.exception(
            "Failed to validate stock"
        )

        return {
            "disponivel": False,
            "message": (
                "Failed to validate stock."
            ),
        }


def get_inventory_overview() -> InventoryOverviewResponse:

    try:
        return (
            _get_inventory_service().get_inventory_overview()
        )

    except Exception:
        logger.exception(
            "Failed to get inventory overview"
        )

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

    try:
        return (
            _get_inventory_service().get_critical_stock_products(
                alert_type=alert_type,
                limit=limit,
            )
        )

    except Exception:
        logger.exception(
            "Failed to get critical products"
        )

        return []
    
def get_inactive_products(
    limit: int = 20,
) -> list[dict]:

    try:
        logger.info(
            "Building inactive products list"
        )

        return _get_inventory_service().get_inactive_products(
            limit=limit
        )

    except Exception:
        logger.exception(
            "Failed to get inactive products"
        )

        return []
    
def get_inventory_diff_by_period(
    reference_period: str,
    reference_date: str = "",
    limit: int = 20,
) -> list[dict]:

    try:
        if not reference_date:
            reference_date = datetime.now().date().isoformat()

        logger.info(
            "Building inventory diff by period | "
            f"date={reference_date} | "
            f"period={reference_period}"
        )

        return _get_inventory_service().get_inventory_diff_by_period(
            reference_date=reference_date,
            reference_period=reference_period,
            limit=limit,
        )

    except Exception:
        logger.exception(
            "Failed to get inventory diff by period"
        )

        return []
