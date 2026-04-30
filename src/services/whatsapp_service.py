import os
import httpx
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


def parse_incoming_message(payload: dict):
    """
    Extrai (phone_number, text) do payload da Meta.
    Retorna (None, None) se não for uma mensagem de texto válida.
    """
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        messages = value.get("messages")
        if not messages:
            return None, None
        msg = messages[0]
        if msg.get("type") != "text":
            return None, None
        return msg["from"], msg["text"]["body"]
    except (KeyError, IndexError):
        return None, None


async def send_message(phone_number: str, text: str) -> dict:
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()
