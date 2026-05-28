import logging
from typing import Any

from src.services.inventory.inventory_service import InventoryService

from src.services.inventory.inventory_types import InventoryAlertReport


logger = logging.getLogger(__name__)


class InventoryAlertService:

    def __init__(self) -> None:
        self.inventory_service = (
            InventoryService()
        )

    def build_inventory_alert_report(
        self,
        low_stock_limit: int = 20,
        out_of_stock_limit: int = 20,
        negative_stock_limit: int = 20,
    ) -> InventoryAlertReport:
        """
        Build a structured inventory alert report.
        """

        return (
            self.inventory_service
            .build_inventory_alert_report(
                low_stock_limit=low_stock_limit,
                out_of_stock_limit=out_of_stock_limit,
                negative_stock_limit=negative_stock_limit,
            )
        )

    @staticmethod
    def format_inventory_alert_email(
        report: InventoryAlertReport,
    ) -> dict[str, str]:
        """
        Convert inventory alert report
        into a readable email payload.
        """

        summary = report.get(
            "summary",
            {},
        )

        low_stock_products = report.get(
            "low_stock_products",
            [],
        )

        out_of_stock_products = report.get(
            "out_of_stock_products",
            [],
        )

        negative_stock_products = report.get(
            "negative_stock_products",
            [],
        )

        subject = (
            "[Alerta de Estoque] "
            f"{summary.get('sem_estoque', 0)} sem estoque | "
            f"{summary.get('abaixo_estoque_minimo', 0)} abaixo do mínimo | "
            f"{summary.get('estoque_negativo', 0)} negativos"
        )

        lines: list[str] = []

        lines.append(
            "Relatório automático de estoque"
        )

        lines.append("")

        lines.append("Resumo geral:")

        lines.append(
            f"- Total de produtos: "
            f"{summary.get('total_produtos', 0)}"
        )

        lines.append(
            f"- Abaixo do estoque mínimo: "
            f"{summary.get('abaixo_estoque_minimo', 0)}"
        )

        lines.append(
            f"- Sem estoque: "
            f"{summary.get('sem_estoque', 0)}"
        )

        lines.append(
            f"- Estoque negativo: "
            f"{summary.get('estoque_negativo', 0)}"
        )

        lines.append(
            f"- Produtos inativos: "
            f"{summary.get('inativos', 0)}"
        )

        lines.append("")

        if out_of_stock_products:

            lines.append(
                "Produtos sem estoque:"
            )

            for product in out_of_stock_products:

                lines.append(
                    f"- {product.get('descricao_completa')} | "
                    f"Qtd: {product.get('quantidade', 0)} | "
                    f"Mínimo: {product.get('estoque_minimo', 0)}"
                )

            lines.append("")

        if negative_stock_products:

            lines.append(
                "Produtos com estoque negativo:"
            )

            for product in negative_stock_products:

                lines.append(
                    f"- {product.get('descricao_completa')} | "
                    f"Qtd: {product.get('quantidade', 0)}"
                )

            lines.append("")

        if low_stock_products:

            lines.append(
                "Produtos abaixo do estoque mínimo:"
            )

            for product in low_stock_products:

                lines.append(
                    f"- {product.get('descricao_completa')} | "
                    f"Qtd: {product.get('quantidade', 0)} | "
                    f"Mínimo: {product.get('estoque_minimo', 0)}"
                )

            lines.append("")

        body = "\n".join(lines)

        logger.info(
            "Inventory alert email formatted"
        )

        return {
            "subject": subject,
            "body": body,
        }