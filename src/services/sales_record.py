import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from src.services.mongo_service import MongoService
from src.config.mongo_config import MongoConfig

logger = logging.getLogger(__name__)

class SalesHistoryService:
    def __init__(self) -> None:
        config = MongoConfig()
        mongo_service = MongoService(config)
        self.collection = mongo_service.get_sales_history_collection()
        
    def save_sale_record(
        self,
        product_name: str,
        quantity: int,
        unit_price: float,
        total_value: float,
        email: str,
        name: str,
        last_name: str,
    ) -> dict[str, Any]:
        """
        Register a sale into the daily diary os sales
        
        Args:
            product_name: Name of the product sold.
            quantity: Quantity sold.
            unit_price: Price per unit of the product.
            total_value: Total value of the sale (quantity * unit_price).
            email: Buyer email.
            name: Buyer first name.
            last_name: Buyer last name.
        
        Returns:
            Saved document in MongoDB
        """
        try:
            today = datetime.now(timezone.utc)
            
            document = {
                "sale_id": str(uuid.uuid4()),
                "date": today,
                "product_name": product_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_value": total_value,
                "email": email,
                "name": name,
                "last_name": last_name,
                "created_at": datetime.now(timezone.utc),
            }
            
            self.collection.insert_one(document)
            logger.info(f"Sale recorded successfully: {document['sale_id']}")
            return document
        
        except Exception:
            logger.exception("Failed to record sale")
            raise
        
    def get_daily_sales(self, date: datetime = None) -> list[dict]:
        """
        Returns all the sales from a specific day
        
        Args:
            date: Date to filter sales. If None, defaults to current day.
        
        Returns:
            List of sales records for the specified day.
        """
        try:
            if date is None:
                date = datetime.now(timezone.utc).date()
                
            sales = list(self.collection.find({"date": date}))
            logger.info(f"Retrieved {len(sales)} sales for date: {date}")
            return sales
        
        except Exception:
            logger.exception("Failed to retrieve daily sales")
            raise
        
        
    def get_sales_summary(
        self,
        date: datetime = None
    ) -> dict[str, Any]:
        """
        Returns sales summary (total, quantity, average) of one day.
        
        Args:
            date: Date to filter sales. If None, defaults to current day.
        
        Returns:
            Dictionary with the sale summary.
        """
        
        try:
            sales = self.get_daily_sales(date)
            
            if not sales:
                return {
                    "date": date or datetime.now(timezone.utc).date(),
                    "total_sales": 0,
                    "total_quantity": 0,
                    "total_value": 0.0,
                    "average_value": 0.0,
                }
            
            total_quantity = sum(s["quantity"] for s in sales)
            total_value = sum(s["total_value"] for s in sales)
            
            return {
                "date": date or datetime.now(timezone.utc).date(),
                "total_sales": len(sales),
                "total_quantity": total_quantity,
                "total_value": total_value,
                "average_value": total_value / len(sales),
            }
            
        except Exception:
            logger.exception("Failed to calculate sales summary")
            raise
    
    