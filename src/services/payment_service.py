import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class MercadoPagoService:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.mercadopago.com"

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=3),
        reraise=True
    )
    async def create_pix_payment(self, amount: float, email: str, first_name: str, last_name: str):
        url = f"{self.base_url}/v1/payments"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "transaction_amount": amount,
            "payment_method_id": "pix",
            "payer": {
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            }
        }

        timeout = httpx.Timeout(10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    url,
                    json=data,
                    headers=headers
                )

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                print("Tempo esgotado para a solicitação. Tentando novamente...")
                raise

            except httpx.HTTPStatusError as e:
                print(f"Erro HTTP: {e.response.status_code} - {e.response.text}")
                print(f"Erro HTTP: {e.response.text}")
                raise

            except Exception as e:
                print(f"Erro inesperado: {str(e)}")
                raise