import logging
from datetime import timezone, datetime
from typing import Any

from src.config.mongo_config import MongoConfig
from src.services.mongo_service import MongoService

logger = logging.getLogger(__name__)

VALID_PERIODS = {"morning", "afternoon", "evening"}

class InventoryService:
    def __init__(self) -> None:
        config = MongoConfig()
        mongo_service = MongoService(config)
        self.snapshot_collection = mongo_service.get_inventory_snapshots_collection(read_only=False)
        self.diff_collection = mongo_service.get_inventory_diff_collection(read_only=False)
        
        self.products_read_collection = mongo_service.get_products_collection(read_only=True)
        self.products_write_collection = mongo_service.get_products_collection(read_only=False)
        
    def save_inventory_snapshot(
        self,
        snapshot_date: str,
        snapshot_period: str,
        product: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Save or update one product inventory snapshot for a specific day and period
            
        Args:
            snapshot_date: Reference day, for example '2026-05-05'.
            snapshot_period: One of 'morning', 'afternoon', 'evening'.
            product: Product document with stock information.

        Returns:
            The snapshot document saved in MongoDB.
        """
        try:
            if snapshot_period not in VALID_PERIODS:
                raise ValueError(
                        f"Invalid snapshot_period: {snapshot_period}. "
                        f"Expected one of {sorted(VALID_PERIODS)}."
                )
                
            document = {
                "snapshot_date": snapshot_date,
                "snapshot_period": snapshot_period,
                "codigo_produto": product["codigo_produto"],
                "descricao_completa": product.get("descricao_completa"),
                "familia_produto": product.get("familia_produto"),
                "quantidade": product.get("quantidade"),
                "estoque_minimo": product.get("estoque_minimo"),
                "preco_sintetico": product.get("preco_sintetico"),
                "created_at": datetime.now(timezone.utc),
            }
                
            self.snapshot_collection.update_one(
                {
                    "snapshot_date": snapshot_date,
                    "snapshot_period": snapshot_period,
                    "codigo_produto": product["codigo_produto"],
                },
                {"$set": document},
                upsert=True,
            )
                
            logger.info(f"Inventory snapshot saved: date={snapshot_date}  period={snapshot_period} product={product['codigo_produto']}")
            return document
            
        except Exception:
            logger.exception("Failed to save inventory snapshot")
            raise
        
    def get_snapshots_by_date_and_period(
        self,
        snapshot_date: str,
        snapshot_period: str,
    ) -> list[dict[str, Any]]:
        """
        Return all inventory snapshots for a specific day and period.
        """
        try:
            snapshots = list(
                self.snapshot_collection.find(
                    {
                        "snapshot_date": snapshot_date,
                        "snapshot_period": snapshot_period,
                    },
                    {"_id": 0},
                )
            )
            
            logger.info(f"Retrieved {len(snapshots)} snapshots for date={snapshot_date} period={snapshot_period}")
            return snapshots
        except Exception:
            logger.exception("Failed to retrieve inventory snapshots")
            raise
        
    def generate_and_save_inventory_diff(
        self,
        reference_date: str,
        reference_period: str,
        previous_date: str,
        previous_period: str,
    ) -> list[dict[str, Any]]:
        """
        Compare two inventory snapshots and persist stock movement per product
        
        Args:
            reference_date: Current snapshot date.
            reference_period: Current snapshot period.
            previous_date: Previous snapshot date.
            previous_period: Previous snapshot period.
        
        Returns:
            List os diff documents saved in MongoDB
        """
        try:
            current_docs = self.get_snapshots_by_date_and_period(
                reference_date,
                reference_period,
            )
            previous_docs = self.get_snapshots_by_date_and_period(
                previous_date,
                previous_period,
            )
            
            previous_map = {
                doc["codigo_produto"]: doc
                for doc in previous_docs
            }
            
            diffs: list[dict[str, Any]] = []
            
            for current in current_docs:
                codigo = current["codigo_produto"]
                previous = previous_map.get(codigo)
                
                estoque_atual = current.get("quantidade") or 0
                estoque_anterior = previous.get("quantidade") if previous else 0
                variacao = estoque_atual - estoque_anterior
                
                document = {
                    "reference_date": reference_date,
                    "reference_period": reference_period,
                    "previous_date": previous_date,
                    "previous_period": previous_period,
                    "codigo_produto": codigo,
                    "descricao_completa": current.get("descricao_completa"),
                    "estoque_anterior": estoque_anterior,
                    "estoque_atual": estoque_atual,
                    "variacao": variacao,
                    "saida_estimada": abs(variacao) if variacao < 0 else 0,
                    "entrada_estimada": variacao if variacao > 0 else 0,
                    "created_at": datetime.now(timezone.utc),
                }
                
                self.diff_collection.update_one(
                    {
                        "reference_date": reference_date,
                        "reference_period": reference_period,
                        "codigo_produto": codigo,
                    },
                    {"$set": document},
                    upsert = True,
                )
                
                diffs.append(document)
            
            logger.info(f"Generated {len(diffs)} inventory diffs for date = {reference_date} ahnd period = {reference_period}")
            return diffs
        
        except Exception:
            logger.exception("Failed to generate inventory diff")
            raise
        
    def get_inventory_diff(
        self,
        reference_date: str,
        reference_period: str,
    ) -> list[dict[str, Any]]:
        """
        Return saved inventory diff documents for a specific day and period
        """
        try:
            diffs = list(
                self.diff_collection.find(
                    {
                        "reference_date": reference_date,
                        "reference_period": reference_period,
                    },
                    {"_id": 0},
                )
            )
            
            logger.info(f"Retrieved {len(diffs)} inventory diffs for date = {reference_date} and period = {reference_period}")
            return diffs
        except Exception:
            logger.exception("Failed to retrieve inventory diffs")
            raise
        
        
    def get_current_stock_by_product_code(
        self,
        product_code: str,  
    ) -> dict | None:
        """
        Return current stock information for a product based on the products collection
        """
        try:
            product = self.products_read_collection.find_one(
                {"codigo_produto": product_code},
                {"_id": 0}
            )
            
            if not product:
                logger.warning(f"Product not found for stock lookup: {product_code}")
                return None
            
            quantidade = product.get("quantidade") or 0
            estoque_minimo = product.get("estoque_minimo") or 0
            
            return {
                "codigo_produto": product["codigo_produto"],
                "descricao_completa": product.get("descricao_completa"),
                "quantidade": quantidade,
                "estoque_minimo": estoque_minimo,
                "produto_inativo": product.get("produto_inativo"),
                "em_estoque": quantidade > 0,
            }
            
        except Exception:
            logger.exception("Failed to retrieve current stock by product code")
            raise
        
    def decrease_stock_after_sale(
        self,
        product_code: str,
        sold_quantity: int,
    ) -> dict:
        """
        Decrease the current stock quantity after an approved sale
        """
        try:
            if sold_quantity <= 0:
                raise ValueError("Sold quantity must be greater then 0")
            
            product = self.products_read_collection.find_one(
                {"codigo_produto": product_code},
                {"_id": 0}
            )
            
            if not product:
                raise ValueError(f"Product not found: {product_code}")
            
            current_quantity = product.get("quantidade") or 0
            new_quantity = current_quantity - sold_quantity
            
            self.products_write_collection.update_one(
                {"codigo_produto": product_code},
                {
                    "$set": {
                        "quantidade": new_quantity,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            
            logger.info(f"Stock updated for product: {product_code} | old = {current_quantity} | new = {new_quantity}")
            
            return {
                "codigo_produto": product_code,
                "quantidade_anterior": current_quantity,
                "quantidade_vendida": sold_quantity,
                "quantidade_atual": new_quantity,
            }
            
        except Exception:
            logger.exception("Failed to decrease stock after sale")
            raise
        
    def get_stock_status_summary(self) -> dict[str, int]:
        """
        Return a high-level summary of current stock conditions.
        """
        try:
            total_products = self.products_read_collection.count_documents({})
            
            low_stock = self.products_read_collection.count_documents(
                {
                    "$expr": {
                        "$lt": ["$quantidade", "$estoque_minimo"]
                    }
                }
            )
            
            out_of_stock = self.products_read_collection.count_documents(
                {
                    "quantidade": 0
                }
            )
            
            negative_stock = self.products_read_collection.count_documents(
                {
                    "quantidade": {"$lt": 0}
                }
            )
            
            inactive_products = self.products_read_collection.count_documents(
                {
                    "produto_inativo": {
                        "$regex": "^sim$",
                        "$option": "i",
                    }
                }
            )
            
            summary = {
                "total_produtos": total_products,
                "abaixo_estoque_minimo": low_stock,
                "sem_estoque": out_of_stock,
                "estoque_negativo": negative_stock,
                "inativos": inactive_products,
            }
            
            logger.info("Stock status summary generated successfully")
            return summary
        
        except Exception:
            logger.exception("Failed to generate stock status summary")
            raise
        
    def get_out_of_stock_products(self, limit: int = 20) -> list[dict[str, Any]]:
        """ 
        Return products with zero stock.
        """
        try:
            products = list(
            self.products_read_collection.collection_find(
                {"quantidade": 0},
                {
                    "_id": 0,
                    "codigo_produto": 1,
                    "descricao_completa": 1,
                    "familia_produto": 1,
                    "unidade": 1,
                    "quantidade": 1,
                    "estoque_minimo": 1,
                    "preco_sintetico": 1,
                },
            ).limit(limit)
        ) 
            
            logger.info(f"Retrieved {len(products)} out of stock products")
            return products
        
        except Exception:
            logger.exception("Failed to retrieve out of stock products")
            raise
        
    def get_negative_stock_products(self, limit:int = 20) -> list[dict[str, Any]]:
        """
        Return products with negatives stock.
        """
        try:
            products = list(
                self.products_read_collection.find(
                    {
                        "quantidade": 0
                    },
                    {
                        "_id": 0,
                        "codigo_produto": 1,
                        "descricao_completa": 1,
                        "familia_produto": 1,
                        "unidade": 1,
                        "quantidade": 1,
                        "estoque_minimo": 1,
                        "preco_sintetico": 1,
                    },
                ).limit(limit)
            )
            
            logger.info(f"Retrieved {len(products)} negative stock products")
            return products
            
        except Exception:
            logger.exception("Failed to retrieve negative stock products")
            raise
        
    def get_low_stock_products(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Return products whose current stock is below the configured minimum stock.
        """
        try:
            products = list(
                self.products_read_collection.find(
                    {
                        "$expr": {
                        "$lt": ["$quantidade", "$estoque_minimo"]
                        }
                    },
                    {
                        "_id": 0,
                        "codigo_produto": 1,
                        "descricao_completa": 1,
                        "familia_produto": 1,
                        "unidade": 1,
                        "quantidade": 1,
                        "estoque_minimo": 1,
                        "preco_sintetico": 1,
                        "produto_inativo": 1,
                    },
                ).limit(limit)
            )
            
            logger.info(f"Retrieved {len(products)} low stock products")
            return products
        
        except Exception:
            logger.exception("Failed to retrieve low stock products")
            raise
    
    def get_inventory_diff_by_period(
        self,
        reference_date: str,
        reference_period: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Return saved inventory diff documents for a specific day
        """
        try:
            diffs = list(
                self.diff_collection.find(
                    {
                        "reference_date": reference_date,
                        "reference_period": reference_period,
                    },
                    {"_id": 0},
                )
                .sort("saida_estimada", -1)
                .limit(limit)
            )
            
            logger.info(f"Retrieved {len(diffs)} inventory diffs for date = {reference_date} and period = {reference_period}")
            return diffs
        
        except Exception:
            logger.exception("Failed to retrieve inventory diffs by period")
            raise