import logging
import uuid

from email_validator import EmailNotValidError, validate_email
from google.adk.tools import ToolContext

from src.services.inventory.inventory_service import InventoryService
from src.services.payment.payment_record import PaymentRecordService
from src.services.sales.sales_record import SalesHistoryService

logger = logging.getLogger(__name__)


def processar_pagamento(
    tool_context: ToolContext,
    valor: float,
    email: str,
    nome: str,
    sobrenome: str,
    quantity: int = 1,
    product_code: str = "",
    product_name: str = "",
    ) -> dict:
    """
    Processa um pagamento PIX para o cliente.

    Use esta ferramenta apenas após o cliente confirmar explicitamente
    que deseja realizar o pagamento e informar os dados necessários.

    Args:
        valor: Valor do pagamento em reais (ex: 150.00)
        email: Email do pagador (ex: "cliente@email.com")
        nome: Primeiro nome do pagador
        sobrenome: Sobrenome do pagador

    Returns:
        dict com:
          - status: situação do pagamento ("pending", "approved", etc.)
          - pix_code: código copia-e-cola do PIX
          - pix_qr_base64: QR code em base64
          - error (opcional): True se houve falha
          - message (opcional): mensagem de erro
    """
    try:
        if valor is None or valor <= 0:
            return {
                "error": True,
                "message": "Payment amount (valor) must be greater than 0.",
            }

        if quantity <= 0:
            return {
                "error": True,
                "message": "Quantity must be greater than 0.",
            }

        try:
            normalized = validate_email(email, check_deliverability=False)
            email = normalized.normalized
        except EmailNotValidError as exc:
            logger.warning("Invalid email provided for payment | error=%s", exc)
            return {
                "error": True,
                "message": "Invalid email address.",
            }

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
            
        if not product_code or not product_name:
            return {
                "error": True,
                "message": "No product is currently selected for payment"
            }
        
        logger.info("Processando pagamento mock de R$ %.2f para %s", valor, email)

        resultado = {
            "status": "approved",
            "pix_code": f"00020101021226880014br.gov.bcb.pix{uuid.uuid4().hex[:20]}",
            "pix_qr_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        }
        
        # Salvar registro de pagamento
        payment_record = PaymentRecordService()
        payment_record.save_payment_record(
            source="mock",
            value=valor,
            email=email,
            name=nome,
            last_name=sobrenome,
            payment_result=resultado,
        )
        
        # Salvar registro de venda
        # venda só é armazenada no DB se for aprovada após o pagamento
        if resultado.get("status") == "approved" and product_code and product_name:
            sales_record = SalesHistoryService()
            inventory_service = InventoryService()
            
            unit_price = valor / quantity if quantity > 0 else valor
            
            sales_record.save_sale_record(
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total_value=valor,
                email=email,
                name=nome,
                last_name=sobrenome,
            )
            
            inventory_service.decrease_stock_after_sale(
                product_code=product_code,
                sold_quantity=quantity,
            )

        return resultado
        
    except Exception:
        logger.exception("Falha ao processar pagamento mock.")
        return {"error": True, "message": "Falha ao processar o pagamento."}
