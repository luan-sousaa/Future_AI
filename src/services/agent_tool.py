from src.services.payment_tool import PaymentTool

async def gerar_pagamento(valor: float, email: str, nome: str, sobrenome: str):
    tool = PaymentTool("SEU_ACCESS_TOKEN")

    try:
        return await tool.create_pix_payment(valor, email, nome, sobrenome)

    except Exception as e:
        return {
            "error": True,
            "message": str(e)
        }