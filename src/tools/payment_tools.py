import logging
import uuid

from email_validator import EmailNotValidError, validate_email
from google.adk.tools import ToolContext

from src.services.cart.cart_service import (
    cart_total,
    clear_cart,
    get_cart,
    item_total,
)
from src.services.inventory.inventory_service import InventoryService
from src.services.payment.payment_record import PaymentRecordService
from src.services.sales.sales_record import SalesHistoryService

logger = logging.getLogger(__name__)


def _mock_pix_result() -> dict:
    return {
        "status": "approved",
        "pix_code": (
            "00020101021226880014br.gov.bcb.pix" + uuid.uuid4().hex[:20]
        ),
        "pix_qr_base64": (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
            "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        ),
    }


def _checkout_cart(
    tool_context: ToolContext,
    cart: list[dict],
    email: str,
    nome: str,
    sobrenome: str,
) -> dict:
    """Checkout itemizado: um pagamento somando o carrinho, um order_id
    compartilhado, uma venda por item e baixa de estoque por item. É o
    order_id comum que faz o grafo de co-ocorrência aprender o que foi
    levado junto."""
    total = cart_total(cart)
    if total <= 0:
        return {"error": True, "message": "Carrinho sem valor a cobrar."}

    order_id = str(uuid.uuid4())
    resultado = _mock_pix_result()

    logger.info(
        "Processando pagamento do carrinho | itens=%d | total=R$ %.2f | "
        "order_id=%s",
        len(cart), total, order_id,
    )

    PaymentRecordService().save_payment_record(
        source="mock",
        value=total,
        email=email,
        name=nome,
        last_name=sobrenome,
        payment_result=resultado,
    )

    if resultado.get("status") == "approved":
        sales_record = SalesHistoryService()
        inventory_service = InventoryService()

        for item in cart:
            code = item.get("codigo_produto")
            quantity = item.get("quantidade") or 0
            if not code or quantity <= 0:
                continue

            sales_record.save_sale_record(
                product_name=item.get("descricao_completa", ""),
                quantity=quantity,
                unit_price=item.get("preco_unitario") or 0.0,
                total_value=item_total(item),
                email=email,
                name=nome,
                last_name=sobrenome,
                order_id=order_id,
                product_code=code,
                familia_produto=item.get("familia_produto"),
            )

            inventory_service.decrease_stock_after_sale(
                product_code=code,
                sold_quantity=quantity,
            )

        clear_cart(tool_context.state)

    return resultado


def _checkout_single(
    tool_context: ToolContext,
    valor: float,
    email: str,
    nome: str,
    sobrenome: str,
    quantity: int,
    product_code: str,
    product_name: str,
) -> dict:
    """Fluxo legado mono-produto: usado quando não há carrinho (cliente leva um
    item só, ou o modelo foi direto ao pagamento sem montar carrinho)."""
    if valor is None or valor <= 0:
        return {
            "error": True,
            "message": "Payment amount (valor) must be greater than 0.",
        }

    if quantity <= 0:
        return {"error": True, "message": "Quantity must be greater than 0."}

    selected_product = tool_context.state.get("selected_product", {})
    last_stock_check = tool_context.state.get("last_stock_check", {})

    if not product_code and selected_product:
        product_code = selected_product.get("codigo_produto", "")
    if not product_code and last_stock_check:
        product_code = last_stock_check.get("codigo_produto", "")
    if not product_code:
        product_code = tool_context.state.get("selected_product_last", "")

    if not product_name and selected_product:
        product_name = selected_product.get("descricao_completa", "")
    if not product_name and last_stock_check:
        product_name = last_stock_check.get("descricao_completa", "")
    if not product_name and product_code:
        for product in tool_context.state.get("last_search_products", []):
            if product.get("codigo_produto") == product_code:
                product_name = product.get("descricao_completa", "")
                break

    # Último recurso: busca pelo código para um código resolvido nunca ser
    # bloqueado por falta de nome.
    if product_code and not product_name:
        product = InventoryService().get_product_by_code(product_code)
        if product:
            product_name = product.get("descricao_completa", "")

    if not product_code or not product_name:
        return {
            "error": True,
            "message": "No product is currently selected for payment",
        }

    logger.info("Processando pagamento mock de R$ %.2f para %s", valor, email)

    resultado = _mock_pix_result()

    PaymentRecordService().save_payment_record(
        source="mock",
        value=valor,
        email=email,
        name=nome,
        last_name=sobrenome,
        payment_result=resultado,
    )

    # venda só é armazenada no DB se for aprovada após o pagamento
    if resultado.get("status") == "approved" and product_code and product_name:
        sales_record = SalesHistoryService()
        inventory_service = InventoryService()

        unit_price = valor / quantity if quantity > 0 else valor

        # Família do item — alimenta o grafo de co-ocorrência. Resolve do
        # estado da sessão; se faltar, busca pelo código.
        familia = (
            selected_product.get("familia_produto")
            or last_stock_check.get("familia_produto")
        )
        if not familia:
            product = InventoryService().get_product_by_code(product_code)
            if product:
                familia = product.get("familia_produto")

        sales_record.save_sale_record(
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            total_value=valor,
            email=email,
            name=nome,
            last_name=sobrenome,
            product_code=product_code,
            familia_produto=familia,
        )

        inventory_service.decrease_stock_after_sale(
            product_code=product_code,
            sold_quantity=quantity,
        )

    return resultado


def processar_pagamento(
    tool_context: ToolContext,
    valor: float = 0.0,
    email: str = "",
    nome: str = "",
    sobrenome: str = "",
    quantity: int = 1,
    product_code: str = "",
    product_name: str = "",
) -> dict:
    """
    Processa um pagamento PIX para o cliente.

    Use apenas após o cliente confirmar explicitamente que deseja pagar e
    informar nome, sobrenome e email. Se houver um carrinho montado
    (add_to_cart), o valor é a SOMA do carrinho — não precisa informar `valor`;
    todos os itens são cobrados num pagamento só e baixados do estoque. Sem
    carrinho, cobra o produto selecionado pelo `valor` informado.

    Returns:
        dict com:
          - status: situação do pagamento ("approved", etc.)
          - pix_code: código copia-e-cola do PIX
          - pix_qr_base64: QR code em base64
          - error (opcional): True se houve falha
          - message (opcional): mensagem de erro
    """
    try:
        try:
            normalized = validate_email(email, check_deliverability=False)
            email = normalized.normalized
        except EmailNotValidError as exc:
            logger.warning("Invalid email provided for payment | error=%s", exc)
            return {"error": True, "message": "Invalid email address."}

        cart = get_cart(tool_context.state)
        if cart:
            return _checkout_cart(
                tool_context, cart, email, nome, sobrenome
            )

        return _checkout_single(
            tool_context,
            valor=valor,
            email=email,
            nome=nome,
            sobrenome=sobrenome,
            quantity=quantity,
            product_code=product_code,
            product_name=product_name,
        )

    except Exception:
        logger.exception("Falha ao processar pagamento mock.")
        return {"error": True, "message": "Falha ao processar o pagamento."}
