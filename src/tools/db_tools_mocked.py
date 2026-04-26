from __future__ import annotations

from src.repositories.product_model import (
    Produto,
    Categoria
    )

import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "repositories" / "price_table.json"


def _load_db() -> dict | None:
    try:
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Database file {DB_PATH} does not exist.")
            
        with DB_PATH.open('r', encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            raise ValueError("The JSON needs to be an object (dictionary) at the top level.")
        
        if "categorias" not in data:
            raise KeyError("The 'categorias' field was not found in the database.")
        
        if not isinstance(data["categorias"], list):
            raise TypeError("The 'categorias' field must be a list.")
        
        return data
    
    except FileNotFoundError:
        logger.exception("Failed to find the database file.")
        return None
        
    except json.JSONDecodeError:
        logger.exception("Invalid JSON or bad encoding in the database file.")
        return None
    
    except Exception:
        logger.exception("Failed to load database.")
        return None

def _find_product_with_category(produto_id: str) -> tuple[Produto, Categoria] | None:
    try:
        if not produto_id or not produto_id.strip():
            return None
        
        produto_id = produto_id.lower().strip()
        
        for categoria in load_categorias():
            for produto in categoria.produtos:
                if produto.id.lower() == produto_id:
                    return produto, categoria
        
        return None
    
    except Exception:
        logger.exception("Failed to find product with category in database.")
        return None
        
def load_categorias() -> list[Categoria]:
    try:
        data = _load_db()
        if data is None:
            return []
        
        categorias: list[Categoria] = []
        
        for categoria_json in data.get("categorias", []):
            produtos: list[Produto] = []
            
            for produto_json in categoria_json.get("produtos", []):
                produto = Produto(
                    id=produto_json.get("id", ""),
                    nome=produto_json.get("nome", ""),
                    especificacao=produto_json.get("especificacao"),
                    unidade_medida=produto_json.get("unidade_medida", ""),
                    precos=produto_json.get("precos", {}),
                )
                
                produtos.append(produto)
            
            categoria = Categoria(
                id=categoria_json.get("id", ""),
                nome=categoria_json.get("nome", ""),
                produtos=produtos,
            )
            categorias.append(categoria)
        
        return categorias
    
    except Exception:
        logger.exception("Failed to load categories from database.")
        return []
    
def list_all_products() -> list[Produto]:
    try:
        categorias = load_categorias()
        produtos: list[Produto] = []
        
        for categoria in categorias:
            produtos.extend(categoria.produtos)
            
        return produtos
    
    except Exception:
        logger.exception("Failed to list all products from database.")
        return []
    
def search_for_product_name(termo: str) -> list[dict]:
    try:
        if not termo or not termo.strip():
            return []

        termo = termo.lower().strip()
        resultados: list[dict] = []

        for categoria in load_categorias():
            for produto in categoria.produtos:
                nome = produto.nome.lower()
                especificacao = (produto.especificacao or "").lower()

                if termo in nome or termo in especificacao:
                    resultados.append(
                        {
                            "id": produto.id,
                            "nome": produto.nome,
                            "especificacao": produto.especificacao,
                            "unidade_medida": produto.unidade_medida,
                            "categoria": categoria.nome,
                        }
                    )

        return resultados

    except Exception:
        logger.exception("Failed to search products by name in database.")
        return []
    
def get_product_by_id(produto_id: str) -> Produto | None:
    try:
        resultado = _find_product_with_category(produto_id)
        if resultado is None:
            return None

        produto, _ = resultado
        return produto

    except Exception:
        logger.exception("Failed to search product by id in database.")
        return None
    
def get_product_details(produto_id: str) -> dict | None:
    try:
        resultado = _find_product_with_category(produto_id)
        if resultado is None:
            return None

        produto, categoria = resultado

        return {
            "id": produto.id,
            "nome": produto.nome,
            "especificacao": produto.especificacao,
            "unidade_medida": produto.unidade_medida,
            "categoria": categoria.nome,
        }

    except Exception:
        logger.exception("Failed to get product details from database.")
        return None
    
def get_prices_summary(produto_id: str) -> dict | None:
    try:
        resultado = _find_product_with_category(produto_id)
        if resultado is None:
            return None
        
        produto, categoria = resultado
        
        precos_ordenados = [
            {"mercado": item.mercado, "preco": item.preco}
            for item in produto.precos_ordenados()
        ]
        
        menor = produto.menor_preco()
        maior = produto.maior_preco()
        
        return {
            "id": produto.id,
            "nome": produto.nome,
            "especificacao": produto.especificacao,
            "unidade_medida": produto.unidade_medida,
            "categoria": categoria.nome,
            "menor_preco": (
                {"mercado": menor.mercado, "preco": menor.preco}
                if menor else None
            ),
            "maior_preco": (
                {"mercado": maior.mercado, "preco": maior.preco}
                if maior else None
            ),
            "quantidade_de_mercados": len(precos_ordenados),
            "precos": precos_ordenados,
        }
        
    except Exception:
        logger.exception("Failed to get price summary for product from database.")
        return None
        
