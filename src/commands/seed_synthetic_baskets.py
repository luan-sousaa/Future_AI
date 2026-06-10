"""Semeia cestas sintéticas em `sales_history` para o grafo de co-ocorrência
ter o que aprender ANTES de existir tráfego real (Fase 2).

Como as cestas saem do próprio mapa de cross-sell (com ruído), o grafo vai em
grande parte RE-APRENDER o mapa — é meio circular. O valor aqui é:
  * provar o pipeline ponta-a-ponta (order_id -> co-ocorrência -> lift -> resolver);
  * demonstrar que o filtro de lift descarta o ruído popular.
Conhecimento NOVO de verdade só vem de uso real.

Tudo é marcado `source: "synthetic"` para limpeza trivial (--reset).

Uso:
    python -m src.commands.seed_synthetic_baskets --orders 500
    python -m src.commands.seed_synthetic_baskets --reset        # só apaga
    python -m src.commands.seed_synthetic_baskets --reset --orders 800 --seed 42
"""
from __future__ import annotations

import argparse
import random
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from src.config.cross_sell import COMPLEMENTARY_FAMILIES
from src.config.mongo_config import MongoConfig
from src.services.mongo.mongo_service import MongoService

SYNTHETIC_SOURCE = "synthetic"

# Probabilidade de um item extra ser um complemento "de verdade" (do mapa).
# O resto é ruído: um produto popular qualquer — é o que o lift deve filtrar.
P_COMPLEMENT = 0.8

# Distribuição do tamanho da cesta (1 item não gera co-ocorrência de propósito).
BASKET_SIZES = [1, 2, 3, 4]
BASKET_WEIGHTS = [0.2, 0.4, 0.25, 0.15]

FAKE_CUSTOMERS = [
    ("ana", "souza"), ("bruno", "lima"), ("carla", "dias"),
    ("diego", "rocha"), ("elaine", "matos"), ("felipe", "alves"),
    ("gisele", "pinto"), ("hugo", "barros"), ("igor", "nunes"),
    ("julia", "ramos"), ("kleber", "costa"), ("livia", "moraes"),
]


def _giro(product: dict) -> float:
    try:
        return float(product.get("venda_ult_13s") or 0) + 1.0  # +1: evita peso 0
    except (TypeError, ValueError):
        return 1.0


def _weighted_choice(products: list[dict]) -> dict:
    return random.choices(products, weights=[_giro(p) for p in products], k=1)[0]


def load_products(products_collection) -> list[dict]:
    return list(
        products_collection.find(
            {
                "quantidade": {"$gt": 0},
                "familia_produto": {"$nin": [None, ""]},
                "produto_inativo": {"$not": {"$regex": "^sim$", "$options": "i"}},
            },
            {
                "_id": 0,
                "codigo_produto": 1,
                "descricao_completa": 1,
                "familia_produto": 1,
                "preco_sintetico": 1,
                "venda_ult_13s": 1,
            },
        )
    )


def build_basket(
    by_family: dict[str, list[dict]],
    anchor_products: list[dict],
    all_products: list[dict],
) -> list[dict]:
    """Monta uma cesta: âncora (pesada por giro) + complementos do mapa + ruído."""
    anchor = _weighted_choice(anchor_products)
    size = random.choices(BASKET_SIZES, weights=BASKET_WEIGHTS, k=1)[0]

    chosen: dict[str, dict] = {anchor["codigo_produto"]: anchor}
    complement_families = COMPLEMENTARY_FAMILIES.get(anchor["familia_produto"], [])

    attempts = 0
    while len(chosen) < size and attempts < size * 5:
        attempts += 1
        use_complement = complement_families and random.random() < P_COMPLEMENT
        if use_complement:
            fam = random.choice(complement_families)
            pool = by_family.get(fam)
            if not pool:
                continue
            candidate = _weighted_choice(pool)
        else:
            candidate = _weighted_choice(all_products)  # ruído popular
        chosen.setdefault(candidate["codigo_produto"], candidate)

    return list(chosen.values())


def make_documents(
    items: list[dict],
    now: datetime,
    days_back: int,
) -> list[dict]:
    order_id = str(uuid.uuid4())
    name, last_name = random.choice(FAKE_CUSTOMERS)
    email = f"{name}.{last_name}@example.com"
    sale_date = now - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )

    docs = []
    for item in items:
        quantity = random.randint(1, 12)
        unit_price = float(item.get("preco_sintetico") or 0) or round(
            random.uniform(3.0, 80.0), 2
        )
        docs.append(
            {
                "sale_id": str(uuid.uuid4()),
                "order_id": order_id,
                "date": sale_date,
                "product_name": item.get("descricao_completa"),
                "product_code": item.get("codigo_produto"),
                "familia_produto": item.get("familia_produto"),
                "quantity": quantity,
                "unit_price": unit_price,
                "total_value": round(unit_price * quantity, 2),
                "email": email,
                "name": name,
                "last_name": last_name,
                "created_at": now,
                "source": SYNTHETIC_SOURCE,
            }
        )
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, default=500, help="nº de cestas")
    parser.add_argument("--days-back", type=int, default=60, help="janela de datas")
    parser.add_argument("--reset", action="store_true", help="apaga sintéticos antes")
    parser.add_argument("--seed", type=int, default=None, help="seed do RNG")
    args = parser.parse_args()

    load_dotenv()
    if args.seed is not None:
        random.seed(args.seed)

    mongo = MongoService(MongoConfig())
    products_collection = mongo.get_products_collection(read_only=True)
    sales_collection = mongo.get_sales_history_collection(read_only=False)

    if args.reset:
        deleted = sales_collection.delete_many({"source": SYNTHETIC_SOURCE})
        print(f"[reset] removidos {deleted.deleted_count} docs sintéticos")

    if args.orders <= 0:
        print("nada a semear (orders <= 0)")
        return

    products = load_products(products_collection)
    if not products:
        print("nenhum produto elegível encontrado — abortando")
        return

    by_family: dict[str, list[dict]] = defaultdict(list)
    for product in products:
        by_family[product["familia_produto"]].append(product)

    # âncoras = produtos cujas famílias têm complementos no mapa
    anchor_products = [
        p for p in products if p["familia_produto"] in COMPLEMENTARY_FAMILIES
    ]
    if not anchor_products:
        print("nenhuma família-âncora do mapa presente no catálogo — abortando")
        return

    now = datetime.now(timezone.utc)
    all_docs: list[dict] = []
    multi_item = 0
    for _ in range(args.orders):
        items = build_basket(by_family, anchor_products, products)
        if len(items) >= 2:
            multi_item += 1
        all_docs.extend(make_documents(items, now, args.days_back))

    sales_collection.insert_many(all_docs)
    print(
        f"[seed] {args.orders} cestas inseridas ({multi_item} multi-item) | "
        f"{len(all_docs)} linhas em sales_history (source={SYNTHETIC_SOURCE})"
    )


if __name__ == "__main__":
    main()
