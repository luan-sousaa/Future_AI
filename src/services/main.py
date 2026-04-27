from fastapi import FastAPI, HTTPException
import asyncio
from .payment_service import MercadoPagoService
from pydantic import BaseModel, EmailStr



app = FastAPI()

ACCESS_TOKEN = "TEST-7156095939817790-042312-65afaf7ac77c9d6ca5b338e862af4cad-210416472"

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
                data.last_name
                ),
            
            timeout=30
        )
        return result

    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Timeout geral")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))