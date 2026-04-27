import logging
import uuid

logger = logging.getLogger(__name__)


def processar_pagamento(valor: float, email: str, nome: str, sobrenome: str) -> dict:
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
        logger.info("Processando pagamento mock de R$ %.2f para %s", valor, email)

        return {
            "status": "pending",
            "pix_code": f"00020101021226880014br.gov.bcb.pix{uuid.uuid4().hex[:20]}",
            "pix_qr_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        }

    except Exception:
        logger.exception("Falha ao processar pagamento mock.")
        return {"error": True, "message": "Falha ao processar o pagamento."}
