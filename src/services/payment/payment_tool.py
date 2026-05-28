import uuid
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class PaymentTool:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.mercadopago.com"

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        reraise=True
    )
    async def create_pix_payment(self, valor: float, email: str, nome: str, sobrenome: str):
        url = f"{self.base_url}/v1/payments"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(uuid.uuid4())
        }

        data = {
            "transaction_amount": valor,
            "description": "Pagamento via agente",
            "payment_method_id": "pix",
            "payer": {
                "email": email,
                "first_name": nome,
                "last_name": sobrenome
            }
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()

        # 🔥 resposta limpa pro agente
        return {
            "status": result.get("status"),
            "pix_code": result["point_of_interaction"]["transaction_data"]["qr_code"],
            "pix_qr_base64": result["point_of_interaction"]["transaction_data"]["qr_code_base64"]
        }