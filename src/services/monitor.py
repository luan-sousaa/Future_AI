import logging
from datetime import datetime

from src.services.inventory.inventory_service import InventoryService
from src.services.inventory.inventory_alert_service import InventoryAlertService
from src.services.email.email_service import EmailNotificationService

logger = logging.getLogger(__name__)

def resolve_period(now: datetime) -> str:
    hour = now.hour
    
    if hour < 12:
        return "morning"
    if hour < 18:
        return "afternoon"
    return "evening"

def get_previous_reference(snapshot_date: str, snapshot_period: str) -> tuple[str, str] | None:
    if snapshot_period == "afternoon":
        return snapshot_date, "morning"
    if snapshot_period == "evening":
        return snapshot_date, "afternoon"
    return None


def run_inventory_monitor() -> dict:
    try:
        inventory_service = InventoryService()
        alert_service = InventoryAlertService()
        
        now = datetime.now()
        snapshot_date = now.date().isoformat()
        snapshot_period = resolve_period(now)
        
        products = list(
            inventory_service.products_read_collection.find({}, {"_id": 0})
        )
        
        logger.info(f"Starting monitoring reference snapshot for {snapshot_date} {snapshot_period} with {len(products)} products")
        
        for product in products:
            inventory_service.save_inventory_snapshot(
                snapshot_date=snapshot_date,
                snapshot_period=snapshot_period,
                product=product,
            )
        
        previous_reference = get_previous_reference(snapshot_date, snapshot_period)
        
        if previous_reference is not None:
            previous_date, previous_period = previous_reference
            inventory_service.generate_and_save_inventory_diff(
                reference_date=snapshot_date,
                reference_period=snapshot_period,
                previous_date=previous_date,
                previous_period=previous_period,
            )
            
        report = alert_service.build_inventory_alert_report()
        
        if not report.get("has_critical_alerts", False):
            logger.info("No inventory alerts for this cycle.")
            return {
                "snapshot_date": snapshot_date,
                "snapshot_period": snapshot_period,
                "has_alert": False,
                "report": report,
                "email_content": None,

            }
        
        email_content = alert_service.format_inventory_alert_email(report)
        
        email_service = EmailNotificationService()
        email_result = email_service.send_email(
            subject=email_content["subject"],
            body=email_content["body"],
        )
        
        logger.info("Inventory alert detected and email processed successfully.")
        result = {
            "snapshot_date": snapshot_date,
            "snapshot_period": snapshot_period,
            "has_alert": True,
            "report": report,
            "email_content": email_content,
            "email_result": email_result,
        }
        
        logger.info(f"Inventory monitor finished successfully")
        return result
    
    except Exception:
        logger.exception("Failed to run inventory monitor.")
        return {
            "has_alert": False,
            "error": True,
            "message": "Failed to run inventory monitor.",
        }
    
