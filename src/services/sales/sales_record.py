import logging
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from src.services.mongo.mongo_service import MongoService
from src.config.mongo_config import MongoConfig

logger = logging.getLogger(__name__)

class SalesHistoryService:
    def __init__(self) -> None:
        config = MongoConfig()
        mongo_service = MongoService(config)
        self.collection = mongo_service.get_sales_history_collection(read_only=False)
        
    def save_sale_record(
        self,
        product_name: str,
        quantity: int,
        unit_price: float,
        total_value: float,
        email: str,
        name: str,
        last_name: str,
        order_id: str | None = None,
        product_code: str | None = None,
        familia_produto: str | None = None,
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
            order_id: Identificador do pedido. Itens comprados juntos (mesma
                cesta) compartilham o mesmo order_id — é o que permite ao grafo
                de co-ocorrência saber o que foi levado junto. Default: um novo
                uuid (pedido de um item só).
            product_code: Código do produto vendido (opcional; alimenta o grafo).
            familia_produto: Família do produto (opcional; granularidade do grafo).

        Returns:
            Saved document in MongoDB
        """
        try:
            sale_date = datetime.now(timezone.utc)

            document = {
                "sale_id": str(uuid.uuid4()),
                "order_id": order_id or str(uuid.uuid4()),
                "date": sale_date,
                "product_name": product_name,
                "product_code": product_code,
                "familia_produto": familia_produto,
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
        
    def get_daily_sales(self, date = None) -> list[dict]:
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

    def get_cooccurrence_complement_families(
        self,
        familia: str,
        limit: int = 3,
        min_cooccurrence: int = 2,
    ) -> list[str]:
        """Famílias que mais são compradas JUNTO da família-âncora, aprendidas
        do histórico (market-basket). Granularidade de família — robusta no
        início, quando co-ocorrência produto-a-produto ainda é esparsa.

        Agrupa as vendas por `order_id` (a cesta), considera só cestas com 2+
        famílias e rankeia os complementos por *lift* = P(B|A) / P(B), mantendo
        apenas associações positivas (lift > 1). O lift derruba itens populares
        que co-ocorrem com tudo por mera frequência.

        Retorna lista vazia enquanto não houver cestas multi-família — é o que
        faz o resolver cair no mapa estático (cold start).

        Args:
            familia: família-âncora (o que o cliente está levando).
            limit: número máximo de famílias complementares retornadas.
            min_cooccurrence: co-ocorrências mínimas para considerar um par
                (evita ruído de cesta única).
        """
        if not familia:
            return []

        try:
            pipeline = [
                {"$match": {"familia_produto": {"$nin": [None, ""]}}},
                {
                    "$group": {
                        "_id": "$order_id",
                        "familias": {"$addToSet": "$familia_produto"},
                    }
                },
                # só cestas com 2+ famílias distintas têm sinal de co-compra
                {"$match": {"familias.1": {"$exists": True}}},
            ]

            baskets = [
                set(doc["familias"])
                for doc in self.collection.aggregate(pipeline)
            ]

            total_baskets = len(baskets)
            if total_baskets == 0:
                return []

            family_orders: Counter = Counter()      # O_B: cestas com a família B
            pair_orders: Counter = Counter()         # O_AB: cestas com âncora + B
            anchor_orders = 0                        # O_A: cestas com a âncora

            for families in baskets:
                for fam in families:
                    family_orders[fam] += 1

                if familia in families:
                    anchor_orders += 1
                    for fam in families:
                        if fam != familia:
                            pair_orders[fam] += 1

            if anchor_orders == 0:
                return []

            scored: list[tuple[str, float, int]] = []
            for fam, o_ab in pair_orders.items():
                if o_ab < min_cooccurrence:
                    continue
                o_b = family_orders[fam]
                if not o_b:
                    continue
                lift = (o_ab * total_baskets) / (anchor_orders * o_b)
                if lift <= 1.0:
                    continue
                scored.append((fam, lift, o_ab))

            # maior lift primeiro; desempata por co-ocorrência absoluta
            scored.sort(key=lambda item: (item[1], item[2]), reverse=True)

            ranked = [fam for fam, _, _ in scored[:limit]]
            logger.info(
                "Co-occurrence complements | familia=%r | baskets=%d | "
                "anchor_orders=%d | ranked=%r",
                familia, total_baskets, anchor_orders, ranked,
            )
            return ranked

        except Exception:
            logger.exception(
                "Failed to compute co-occurrence complements | familia=%r",
                familia,
            )
            return []

