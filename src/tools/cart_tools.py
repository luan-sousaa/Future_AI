import logging
from typing import Any

from google.adk.tools import ToolContext

from src.services.cart.cart_service import (
    add_item,
    cart_summary,
    get_cart,
    remove_item,
)
from src.tools.mongo_tools import _get_inventory_service, _resolve_product_code

logger = logging.getLogger(__name__)


def _resolve_product_details(
    tool_context: ToolContext,
    product_code: str,
) -> dict[str, Any]:
    """Nome, família e preço do produto — do estado da sessão, com fallback no
    banco para nunca montar uma linha de carrinho incompleta."""
    selected = tool_context.state.get("selected_product", {})
    if selected.get("codigo_produto") == product_code and selected.get(
        "preco_sintetico"
    ) is not None:
        return {
            "descricao_completa": selected.get("descricao_completa", ""),
            "familia_produto": selected.get("familia_produto"),
            "preco_sintetico": selected.get("preco_sintetico"),
        }

    product = _get_inventory_service().get_product_by_code(product_code)
    if not product:
        return {}
    return {
        "descricao_completa": product.get("descricao_completa", ""),
        "familia_produto": product.get("familia_produto"),
        "preco_sintetico": product.get("preco_sintetico"),
    }


def add_to_cart(
    tool_context: ToolContext,
    quantity: int,
) -> dict[str, Any]:
    """Adiciona ao carrinho o produto atualmente selecionado na conversa, na
    quantidade informada. Use sempre que o cliente confirmar que quer um item
    (inclusive um complemento que ele aceitou levar). O código do produto é
    resolvido internamente do estado — o agente só informa a quantidade.
    Valida estoque antes de adicionar. Re-adicionar o mesmo produto atualiza a
    quantidade."""
    try:
        if quantity is None or quantity <= 0:
            return {"error": True, "message": "Quantidade deve ser maior que 0."}

        product_code = _resolve_product_code(tool_context, "")
        if not product_code:
            return {
                "error": True,
                "message": "Nenhum produto selecionado para adicionar.",
            }

        availability = _get_inventory_service().validate_stock_availability(
            product_code, quantity
        )
        if not availability.get("disponivel"):
            return {
                "error": True,
                "message": "Estoque insuficiente para a quantidade pedida.",
                "quantidade_disponivel": availability.get("quantidade_disponivel"),
            }

        details = _resolve_product_details(tool_context, product_code)
        if not details:
            return {
                "error": True,
                "message": "Produto não encontrado para adicionar ao carrinho.",
            }

        add_item(
            tool_context.state,
            codigo_produto=product_code,
            descricao_completa=details["descricao_completa"],
            familia_produto=details.get("familia_produto"),
            quantidade=quantity,
            preco_unitario=float(details.get("preco_sintetico") or 0.0),
        )

        logger.info(
            "Item added to cart | code=%r | qty=%d", product_code, quantity
        )
        return cart_summary(get_cart(tool_context.state))

    except Exception:
        logger.exception("Failed to add item to cart")
        return {"error": True, "message": "Falha ao adicionar ao carrinho."}


def view_cart(tool_context: ToolContext) -> dict[str, Any]:
    """Mostra os itens do carrinho e o total atual. Use antes de fechar o
    pedido para confirmar com o cliente."""
    try:
        return cart_summary(get_cart(tool_context.state))
    except Exception:
        logger.exception("Failed to view cart")
        return {"error": True, "message": "Falha ao ler o carrinho."}


def remove_from_cart(
    tool_context: ToolContext,
    product_code: str,
) -> dict[str, Any]:
    """Remove um produto do carrinho pelo código. Use quando o cliente desistir
    de um item."""
    try:
        remove_item(tool_context.state, product_code)
        logger.info("Item removed from cart | code=%r", product_code)
        return cart_summary(get_cart(tool_context.state))
    except Exception:
        logger.exception("Failed to remove item from cart")
        return {"error": True, "message": "Falha ao remover do carrinho."}
