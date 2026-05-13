import os
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from .payment_service import MercadoPagoService
from .whatsapp_service import parse_incoming_message, send_message

load_dotenv()

app = FastAPI()

ACCESS_TOKEN = "TEST-7156095939817790-042312-65afaf7ac77c9d6ca5b338e862af4cad-210416472"
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")

service = MercadoPagoService(ACCESS_TOKEN)


class PaymentRequest(BaseModel):
    valor: float
    email: EmailStr
    first_name: str
    last_name: str


@app.post("/pagar")
async def pagar(data: PaymentRequest):
    try:
        result = await asyncio.wait_for(
            service.create_pix_payment(
                data.valor,
                data.email,
                data.first_name,
                data.last_name,
            ),
            timeout=30,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Timeout geral")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/webhook")
async def verify_webhook(request: Request):
    """Endpoint de verificação exigido pela Meta ao configurar o webhook."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)

    raise HTTPException(status_code=403, detail="Forbidden")


@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    """Recebe mensagens do WhatsApp enviadas pela Meta, processa com o agente e responde."""
    payload = await request.json()
    phone, text = parse_incoming_message(payload)

    if not phone or not text:
        return {"status": "ignored"}

    response_text = await process_message(phone, text)
    await send_message(phone, response_text)

    return {"status": "ok"}