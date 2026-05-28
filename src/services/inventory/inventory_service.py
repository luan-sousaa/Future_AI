import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, TypedDict

from pymongo.errors import PyMongoError

from src.config.alerts.alert_manager import AlertTypeManager
from src.services.inventory.inventory_types import InventoryAlertReport, InventoryOverviewResponse
from src.config.alerts.alert_enums import AlertTypeEnum
from src.config.mongo_config import MongoConfig
from src.services.mongo.mongo_service import MongoService

logger = logging.getLogger(__name__)


class InventoryPeriod(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"


class ProductStock(TypedDict):
    codigo_produto: str
    descricao_completa: str
    quantidade: int
    estoque_minimo: int
    produto_inativo: str
    em_estoque: bool


class InventoryService:
    def __init__(self) -> None:
        config = MongoConfig()
        mongo_service = MongoService(config)

        self.snapshot_collection = (
            mongo_service.get_inventory_snapshots_collection(
                read_only=False
            )
        )

        self.diff_collection = (
            mongo_service.get_inventory_diff_collection(
                read_only=False
            )
        )

        self.products_read_collection = (
            mongo_service.get_products_collection(
                read_only=True
            )
        )

        self.products_write_collection = (
            mongo_service.get_products_collection(
                read_only=False
            )
        )

    @staticmethod
    def _build_product_projection() -> dict[str, int]:
        return {
            "_id": 0,
            "codigo_produto": 1,
            "descricao_completa": 1,
            "familia_produto": 1,
            "unidade": 1,
            "quantidade": 1,
            "estoque_minimo": 1,
            "preco_sintetico": 1,
            "produto_inativo": 1,
        }

    @staticmethod
    def _build_snapshot_key(
        snapshot_date: str,
        snapshot_period: str,
        product_code: str,
    ) -> dict[str, str]:
        return {
            "snapshot_date": snapshot_date,
            "snapshot_period": snapshot_period,
            "codigo_produto": product_code,
        }

    def save_inventory_snapshot(
        self,
        snapshot_date: str,
        snapshot_period: str,
        product: dict[str, Any],
    ) -> dict[str, Any]:
        product_code = product.get("codigo_produto")

        if not product_code:
            raise ValueError("Product must have codigo_produto.")

        document = {
            **self._build_snapshot_key(
                snapshot_date=snapshot_date,
                snapshot_period=snapshot_period,
                product_code=product_code,
            ),
            "descricao_completa": product.get("descricao_completa", ""),
            "familia_produto": product.get("familia_produto"),
            "unidade": product.get("unidade"),
            "quantidade": product.get("quantidade", 0),
            "estoque_minimo": product.get("estoque_minimo", 0),
            "preco_sintetico": product.get("preco_sintetico"),
            "produto_inativo": product.get("produto_inativo", ""),
            "captured_at": datetime.now(timezone.utc),
        }

        try:
            self.snapshot_collection.update_one(
                self._build_snapshot_key(
                    snapshot_date=snapshot_date,
                    snapshot_period=snapshot_period,
                    product_code=product_code,
                ),
                {"$set": document},
                upsert=True,
            )

            return document

        except PyMongoError:
            logger.exception(
                "Failed to save inventory snapshot"
            )
            raise

    def generate_and_save_inventory_diff(
        self,
        reference_date: str,
        reference_period: str,
        previous_date: str,
        previous_period: str,
    ) -> list[dict[str, Any]]:
        try:
            current_snapshots = list(
                self.snapshot_collection.find(
                    {
                        "snapshot_date": reference_date,
                        "snapshot_period": reference_period,
                    },
                    {"_id": 0},
                )
            )

            previous_snapshots = list(
                self.snapshot_collection.find(
                    {
                        "snapshot_date": previous_date,
                        "snapshot_period": previous_period,
                    },
                    {"_id": 0},
                )
            )

            previous_by_code = {
                item["codigo_produto"]: item
                for item in previous_snapshots
                if item.get("codigo_produto")
            }

            diffs: list[dict[str, Any]] = []

            for current in current_snapshots:
                product_code = current.get("codigo_produto")

                if not product_code:
                    continue

                previous = previous_by_code.get(product_code)
                previous_quantity = (
                    previous.get("quantidade", 0)
                    if previous
                    else 0
                )
                current_quantity = current.get("quantidade", 0)
                difference = current_quantity - previous_quantity

                if difference == 0:
                    movement_type = "unchanged"
                elif difference > 0:
                    movement_type = "increase"
                else:
                    movement_type = "decrease"

                diffs.append(
                    {
                        "reference_date": reference_date,
                        "reference_period": reference_period,
                        "previous_date": previous_date,
                        "previous_period": previous_period,
                        "codigo_produto": product_code,
                        "descricao_completa": current.get(
                            "descricao_completa",
                            "",
                        ),
                        "familia_produto": current.get(
                            "familia_produto"
                        ),
                        "unidade": current.get("unidade"),
                        "quantidade_anterior": previous_quantity,
                        "quantidade_atual": current_quantity,
                        "diferenca": difference,
                        "diferenca_absoluta": abs(difference),
                        "movement_type": movement_type,
                        "created_at": datetime.now(timezone.utc),
                    }
                )

            self.diff_collection.delete_many(
                {
                    "reference_date": reference_date,
                    "reference_period": reference_period,
                    "previous_date": previous_date,
                    "previous_period": previous_period,
                }
            )

            if diffs:
                self.diff_collection.insert_many(diffs)

            logger.info(
                "Inventory diff generated successfully",
                extra={
                    "reference_date": reference_date,
                    "reference_period": reference_period,
                    "previous_date": previous_date,
                    "previous_period": previous_period,
                    "diffs": len(diffs),
                },
            )

            return diffs

        except PyMongoError:
            logger.exception(
                "Failed to generate inventory diff"
            )
            raise

    def get_inventory_diff_by_period(
        self,
        reference_date: str,
        reference_period: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        try:
            cursor = (
                self.diff_collection.find(
                    {
                        "reference_date": reference_date,
                        "reference_period": reference_period,
                    },
                    {"_id": 0},
                )
                .sort("diferenca_absoluta", -1)
                .limit(limit)
            )

            return list(cursor)

        except PyMongoError:
            logger.exception(
                "Failed to retrieve inventory diff"
            )
            raise

    def get_product_by_code(
        self,
        product_code: str,
    ) -> dict[str, Any] | None:
        try:
            return self.products_read_collection.find_one(
                {"codigo_produto": product_code},
                self._build_product_projection(),
            )

        except PyMongoError:
            logger.exception(
                "Failed to fetch product by code"
            )
            raise

    def search_products_by_name(
        self,
        term: str,
        limit: int = 10,
        skip: int = 0,
    ) -> list[dict[str, Any]]:

        import re

        try:
            escaped_term = re.escape(term.strip())

            cursor = (
                self.products_read_collection.find(
                    {
                        "descricao_completa": {
                            "$regex": escaped_term,
                            "$options": "i",
                        }
                    },
                    self._build_product_projection(),
                )
                .skip(skip)
                .limit(limit)
            )

            return list(cursor)

        except PyMongoError:
            logger.exception(
                "Failed to search products"
            )
            raise

    def get_products_by_codes(
        self,
        product_codes: list[str],
    ) -> list[dict[str, Any]]:

        try:
            if not product_codes:
                return []

            products = list(
                self.products_read_collection.find(
                    {
                        "codigo_produto": {
                            "$in": product_codes
                        }
                    },
                    self._build_product_projection(),
                )
            )

            return products

        except PyMongoError:
            logger.exception(
                "Failed to fetch products by codes"
            )
            raise

    def get_current_stock_by_product_code(
        self,
        product_code: str,
    ) -> ProductStock | None:

        try:
            product = self.get_product_by_code(
                product_code
            )

            if not product:
                return None

            quantidade = product.get(
                "quantidade",
                0,
            )

            estoque_minimo = product.get(
                "estoque_minimo",
                0,
            )

            return {
                "codigo_produto": product[
                    "codigo_produto"
                ],
                "descricao_completa": product.get(
                    "descricao_completa",
                    "",
                ),
                "quantidade": quantidade,
                "estoque_minimo": estoque_minimo,
                "produto_inativo": product.get(
                    "produto_inativo",
                    "",
                ),
                "em_estoque": quantidade > 0,
            }

        except PyMongoError:
            logger.exception(
                "Failed to retrieve stock"
            )
            raise

    def validate_stock_availability(
        self,
        product_code: str,
        requested_quantity: int,
    ) -> dict[str, Any]:

        if requested_quantity <= 0:
            raise ValueError(
                "requested_quantity must be greater than 0"
            )

        stock_info = (
            self.get_current_stock_by_product_code(
                product_code
            )
        )

        if stock_info is None:
            return {
                "disponivel": False,
                "message": "Product not found.",
            }

        available_quantity = stock_info[
            "quantidade"
        ]

        is_available = (
            available_quantity >= requested_quantity
        )

        return {
            "codigo_produto": product_code,
            "disponivel": is_available,
            "quantidade_disponivel": available_quantity,
            "quantidade_solicitada": requested_quantity,
            "message": (
                "Requested quantity is available."
                if is_available
                else "Insufficient stock."
            ),
        }

    def decrease_stock_after_sale(
        self,
        product_code: str,
        sold_quantity: int,
    ) -> dict[str, Any]:

        if sold_quantity <= 0:
            raise ValueError(
                "sold_quantity must be greater than 0"
            )

        try:
            result = (
                self.products_write_collection.update_one(
                    {
                        "codigo_produto": product_code,
                        "quantidade": {
                            "$gte": sold_quantity
                        },
                    },
                    {
                        "$inc": {
                            "quantidade": -sold_quantity
                        },
                        "$set": {
                            "updated_at": datetime.now(
                                timezone.utc
                            )
                        },
                    },
                )
            )

            if result.modified_count == 0:
                raise ValueError(
                    "Insufficient stock or product not found."
                )

            updated_product = (
                self.get_current_stock_by_product_code(
                    product_code
                )
            )

            logger.info(
                "Stock updated successfully",
                extra={
                    "product_code": product_code,
                    "sold_quantity": sold_quantity,
                },
            )

            return {
                "codigo_produto": product_code,
                "quantidade_atual": updated_product[
                    "quantidade"
                ],
            }

        except PyMongoError:
            logger.exception(
                "Failed to decrease stock"
            )
            raise

    def get_inventory_overview(
        self,
    ) -> InventoryOverviewResponse:

        try:
            total_products = (
                self.products_read_collection.count_documents(
                    {}
                )
            )

            low_stock = (
                self.products_read_collection.count_documents(
                    {
                        "$expr": {
                            "$lt": [
                                "$quantidade",
                                "$estoque_minimo",
                            ]
                        }
                    }
                )
            )

            out_of_stock = (
                self.products_read_collection.count_documents(
                    {"quantidade": 0}
                )
            )

            negative_stock = (
                self.products_read_collection.count_documents(
                    {"quantidade": {"$lt": 0}}
                )
            )

            inactive_products = (
                self.products_read_collection.count_documents(
                    {
                        "produto_inativo": {
                            "$regex": "^sim$",
                            "$options": "i",
                        }
                    }
                )
            )

            summary = {
                "total_produtos": total_products,
                "abaixo_estoque_minimo": low_stock,
                "sem_estoque": out_of_stock,
                "estoque_negativo": negative_stock,
                "inativos": inactive_products,
            }

            status = "healthy"

            if (
                negative_stock > 0
                or out_of_stock > 0
            ):
                status = "critical"

            elif low_stock > 0:
                status = "attention"

            return {
                "summary": summary,
                "status": status,
            }

        except PyMongoError:
            logger.exception(
                "Failed to build inventory overview"
            )
            raise

    def get_critical_stock_products(
        self,
        alert_type: AlertTypeEnum,
        limit: int = 20,
    ) -> list[dict[str, Any]]:

        try:
            normalized_alert_type = (
                AlertTypeManager.normalize(
                    alert_type
                )
            )

            if not AlertTypeManager.is_valid(
                normalized_alert_type
            ):
                raise ValueError(
                    f"Invalid alert_type: {alert_type}"
                )

            query = (
                AlertTypeManager.get_mongodb_query(
                    normalized_alert_type
                )
            )

            products = list(
                self.products_read_collection.find(
                    query,
                    self._build_product_projection(),
                ).limit(limit)
            )

            logger.info(
                "Critical stock query executed",
                extra={
                    "alert_type": normalized_alert_type,
                    "products_found": len(products),
                },
            )

            return products

        except ValueError:
            raise

        except PyMongoError:
            logger.exception(
                "Failed to retrieve critical products"
            )
            raise
    
    def get_inactive_products(
        self,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Return inactive products.
        """

        try:
            products = list(
                self.products_read_collection.find(
                    {
                        "produto_inativo": {
                            "$regex": "^sim$",
                            "$options": "i",
                        }
                    },
                    self._build_product_projection(),
                ).limit(limit)
            )

            logger.info(
                f"Retrieved {len(products)} inactive products"
            )

            return products

        except Exception:
            logger.exception(
                "Failed to retrieve inactive products"
            )
            raise
    
    def build_inventory_alert_report(
        self,
        low_stock_limit: int = 20,
        out_of_stock_limit: int = 20,
        negative_stock_limit: int = 20,
    ) -> InventoryAlertReport:
        """
        Build a complete inventory alert report.

        This method centralizes all inventory alert queries
        into a single structured payload optimized for agents.
        """

        try:
            overview = self.get_inventory_overview()
            summary = overview["summary"]

            low_stock_products = (
                self.get_critical_stock_products(
                    alert_type="low_stock",
                    limit=low_stock_limit,
                )
            )

            out_of_stock_products = (
                self.get_critical_stock_products(
                    alert_type="out_of_stock",
                    limit=out_of_stock_limit,
                )
            )

            negative_stock_products = (
                self.get_critical_stock_products(
                    alert_type="negative_stock",
                    limit=negative_stock_limit,
                )
            )

            has_critical_alerts = any([
                summary.get(
                    "abaixo_estoque_minimo",
                    0,
                ) > 0,

                summary.get(
                    "sem_estoque",
                    0,
                ) > 0,

                summary.get(
                    "estoque_negativo",
                    0,
                ) > 0,
            ])

            report: InventoryAlertReport = {
                "has_critical_alerts": (
                    has_critical_alerts
                ),

                "summary": summary,

                "low_stock_products": (
                    low_stock_products
                ),

                "out_of_stock_products": (
                    out_of_stock_products
                ),

                "negative_stock_products": (
                    negative_stock_products
                ),
            }

            logger.info(
                "Inventory alert report built successfully"
            )

            return report

        except Exception:
            logger.exception(
                "Failed to build inventory alert report"
            )
            raise
