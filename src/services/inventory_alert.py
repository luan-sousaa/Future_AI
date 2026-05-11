import logging
from typing import Any

from src.services.inventory import InventoryService

logger = logging.getLogger(__name__)

class InventoryAlertService:
    def __init__(self) -> None:
        self.inventory_service = InventoryService()
        
    
    def build_inventory_alert_report(
        self,
        low_stock_limit: int = 20,
        out_of_stock_limit: int = 20,
        negative_stock_limit: int = 20,
    ) -> dict[str, Any]:
        """
        Build a structured inventory alert report based on current stock conditions
        """
        try:
            summary = self.inventory_service.get_stock_status_summary()
            low_stock_products = self.inventory_service.get_low_stock_products(limit=low_stock_limit)
            out_of_stock_products = self.inventory_service.get_out_of_stock_products(limit=out_of_stock_limit)
            negative_stock_products = self.inventory_service.get_negative_stock_products(limit=negative_stock_limit)
            
            has_alert = any([
                summary.get("abaixo_estoque_minimo", 0) > 0,
                summary.get("sem_estoque", 0) > 0,
                summary.get("estoque_negativo", 0) > 0,
            ])
            
            report = {
                "has_alert": has_alert,
                "summary": summary,
                "low_stock_products": low_stock_products,
                "out_of_stock_products": out_of_stock_products,
                "negative_stock_products": negative_stock_products,
            }
            
            logger.info("Inventory alert report built successfully")
            return report
        
        except Exception:
            logger.exception("Error building inventory alert report")
            raise
        
    def format_inventory_alert_email(report: dict) -> dict[str, str]:
        """
        Build email subject and body from an inventory alert report.
        """
        summary = report.get("summary", {})
        low_stock_products = report.get("low_stock_products", [])
        out_of_stock_products = report.get("out_of_stock_products", [])
        negative_stock_products = report.get("negative_stock_products", [])
        
        subject = (
            f"""
            [Alerta de Estoque]
            {summary.get('sem_estoque', 0)} sem estoque,
            {summary.get('abaixo_estoque_minimo', 0)} abaixo do mínimo,
            {summary.get('estoque_negativo', 0)} com estoque negativo
            """
        )
        
        lines: list[str] = []
        lines.append("Relatório automático de monitoramento de estoque")
        lines.append("")
        lines.append("Resumo geral:")
        lines.append(f"- Total de produtos: {summary.get('total_produtos', 0)}")
        lines.append(f"- Abaixo do estoque mínimo: {summary.get('abaixo_estoque_minimo', 0)}")
        lines.append(f"- Sem estoque: {summary.get('sem_estoque', 0)}")
        lines.append(f"- Estoque negativo: {summary.get('estoque_negativo', 0)}")
        lines.append(f"- Inativos: {summary.get('inativos', 0)}")
        lines.append("")
        
        if out_of_stock_products:
            lines.append("Produtos sem estoque:")
            for product in out_of_stock_products:
                lines.append(
                    f"""
                    - {product.get('descricao_completa')} |
                    Qtd: {product.get('quantidade', 0)} |
                    Mínimo: {product.get('estoque_minimo', 0)}
                    """
                )
            
            lines.append("")
        
        if negative_stock_products:
            lines.append("Produtos com estoque negativo:")
            for product in negative_stock_products:
                lines.append(
                    f"""
                    - {product.get('descricao_completa')} |
                    Qtd: {product.get('quantidade', 0)} 
                    """
                )
            
            lines.append("")
            
        if low_stock_products:
            lines.append("Produtos abaixo do estoque mínimo:")
            for product in low_stock_products:
                lines.append(
                    f"""
                    - {product.get('descricao_completa')} |
                    Qtd: {product.get('quantidade', 0)} |
                    Mínimo: {product.get('estoque_minimo', 0)}
                    """
                )
                
            lines.append("")
        
        body = "\n".join(lines)
        
        return {
            "subject": subject,
            "body": body,
        }