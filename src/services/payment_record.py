import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from src.services.mongo_service import MongoService
from src.config.mongo_config import MongoConfig

logger = logging.getLogger(__name__)

class PaymentRecordService:
    def __init__(self) -> None:
        config = MongoConfig()
        mongo_service = MongoService(config)
        self.collection = mongo_service.get_payments_collection()
        
    def save_payment_record(
        self,
        source: str,
        value: float,
        email: str,
        name: str,
        last_name: str,
        payment_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Save payment attempt/result into the payment collection
            
        Args:
            source: Origin of the payment flow, such as "mock" or "mercado_pago".
            valor: Payment amount.
            email: Payer email.
            nome: Payer first name.
            sobrenome: Payer last name.
            payment_result: Result returned by the payment processor/tool.
            
        Returns:
            The document saved in MongoDB
        """
        try:
            document = {
                "payment_id": str(uuid.uuid4()),
                "source": source,
                "status": payment_result.get("status"),
                "value": value,
                "email": email,
                "name": name,
                "last_name": last_name,
                "pix_code": payment_result.get("pix_code"),
                "pix_qr_base64": payment_result.get("pix_qr_base64"),
                "error": payment_result.get("error", False),
                "message": payment_result.get("message"),
                "gateway_response": payment_result,
                "created_at": datetime.now(timezone.utc),
            }
                
            self.collection.insert_one(document)
            logger.info(f"Payment record saved successfully: {document['payment_id']}")
            return document
            
        except Exception:
                logger.exception("Failed to save payment record")
                raise
                
                            