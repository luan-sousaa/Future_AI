import logging
from typing import Optional 

from google.adk.tools import ToolContext

from src.config.mongo_config import MongoConfig
from src.services.mongo_service import MongoService
from src.services.inventory import InventoryService

logger = logging.getLogger(__name__)

# Helpers
def _get_products_collection():
    config = MongoConfig()
    mongo_service = MongoService(config)
    return mongo_service.get_products_collection(read_only=True)

def _get_product_by_code(product_code: str) -> Optional[dict]:
    """
    Fetch one exact product by code 
    """
    try:
        logger.info(f"Fetching product by code: {product_code}")
        
        if not product_code or not product_code.strip():
            logger.warning("Empty product code.")
            return None
        
        collection = _get_products_collection()
        
        produto = collection.find_one(
            {"codigo_produto": product_code},
            {"_id": 0}
        )
        
        if not produto:
            logger.warning(f"No product found with code: {product_code}")
            return None
        
        logger.info(f"Product found: {produto['descricao_completa']}")
        return produto 
    
    except Exception:
        logger.exception("Failed to fetch product by code from MongoDB.")
        return None
    
    
# Ferramentas
def search_product_by_name(
    tool_context: ToolContext,
    term: str,
    limit: int = 10,
) -> list[dict]:
    """
    Search products by name or description in MongoDB and store the last search results in session state.
    """
    try:
        logger.info(f"Searching products with term: {term}")
        
        if not term or not term.strip():
            logger.warning("Empty search term")
            return []
        
        collection = _get_products_collection()
        
        cursor = collection.find(
            {
                "descricao_completa": {
                    "$regex": term,
                    "$options": "i",
                }
            },
            {
                "_id": 0,
                "codigo_produto": 1,
                "descricao_completa": 1,
                "familia_produto": 1,
                "unidade": 1,
                "preco_sintetico": 1,
            },
        ).limit(limit)
        
        full_records = list(cursor)
        client_records = [
            {
                "descricao_completa": item["descricao_completa"],
                "familia_produto": item.get("familia_produto"),
                "unidade": item.get("unidade"),
                "preco_sintetico": item.get("preco_sintetico"),
            }
            for item in full_records
        ]
        
        tool_context.state["last_search_term"] = term
        tool_context.state["last_search_results"] = full_records
        
        logger.info(f"Found {len(full_records)} matching MongoDB products")
        return client_records
    
    except Exception:
        logger.exception("Failed to search products by name in MongoDB")
        return []
    
def get_product_by_code(
    tool_context: ToolContext,
    product_code: str,
) -> Optional[dict]:
    """
    Select one product by exact code and store it in session state
    """
    try:
        logger.info(f"Selecting product by code from MongoDB: {product_code}")
        
        produto = _get_product_by_code(product_code)
        if produto is None:
            return None
    
        selected_codes = tool_context.state.get("selected_product_codes", [])
        selected_products = tool_context.state.get("selected_products", [])
        
        if produto["codigo_produto"] not in selected_codes:
            selected_codes.append(produto["codigo_produto"])
            selected_products.append(produto)
            logger.info(f"Product code {product_code} added to current selection")
        else:
            logger.info(f"Product code {product_code} already exists in current selection")
            
            
        tool_context.state["selected_product_codes"] = selected_codes
        tool_context.state["selected_products"] = selected_products
        tool_context.state["selected_product_last"] = produto
        
        client_result = {
            "descricao_completa": produto["descricao_completa"],
            "familia_produto": produto.get("familia_produto"),
            "unidade": produto.get("unidade"),
        }

        logger.info(f"Total selected products: {len(selected_products)}")
        return client_result

    except Exception:
        logger.exception("Failed to select product by code from MongoDB")
        return None
    
def get_product_stock_and_price_summary(
    tool_context: ToolContext,
) -> list[dict]:
    """
    Return stock and price summaries for the currently selected MongoDB products.
    """
    try:
        logger.info("Building stock and price summary for MongoDB products")
        
        selected_codes = tool_context.state.get("selected_product_codes", [])
        
        if not selected_codes:
            logger.warning("No selected product codes found in session state")
            return []
        
        full_summaries: list[dict] = []
        client_summaries: list[dict] = []
        
        for code in selected_codes:
            produto = _get_product_by_code(code)
            if produto is None:
                logger.warning(f"Skipping missing product code during summary: {code}")
                continue            
            
            full_summary = {
                "codigo_produto": produto["codigo_produto"],
                "descricao_completa": produto["descricao_completa"],
                "familia_produto": produto.get("familia_produto"),
                "unidade": produto.get("unidade"),
                "produto_inativo": produto.get("produto_inativo"),
                "quantidade_em_estoque": produto.get("quantidade"),
                "estoque_minimo": produto.get("estoque_minimo"),
                "preco_sintetico": produto.get("preco_sintetico"),
            }
            
            client_summary = {
                "descricao_completa": produto["descricao_completa"],
                "familia_produto": produto.get("familia_produto"),
                "unidade": produto.get("unidade"),
                "preco_sintetico": produto.get("preco_sintetico"),
            }
            
            full_summaries.append(full_summary)
            client_summaries.append(client_summary)
        
        tool_context.state["last_products_summary"] = full_summaries
        
        logger.info(f"Built summaries for {len(client_summaries)} MongoDB products")
        return client_summaries
    
    except Exception:
        logger.exception("Failed to build stock and price summary from MongoDB.")
        return []
    

def get_low_stock_products(limit: int = 20) -> list[dict]:
    """
    Return products whose stock is below the minimum configured value.
    """
    try:
        logger.info("Searching low stock products in MongoDB")
        
        collection = _get_products_collection()
        
        cursor = collection.find(
            {
                "$expr": {
                    "$lt": ["$quantidade", "$estoque_minimo"]
                }
            },
            {
                "_id": 0,
                "codigo_produto": 1,
                "descricao_completa": 1,
                "quantidade": 1,
                "estoque_minimo": 1,
                "preco_sintetico": 1,
            },
        ).limit(limit)
        
        records = list(cursor)
        
        logger.info(f"Found {len(records)} low stock MongoDB products")
        return records
    
    except Exception:
        logger.exception("Failed to get low stock products from MongoDB.")
        return []
    
def get_inactive_products(limit: int = 20) -> list[dict]:
    """
    Return inactive products for catalog review
    """
    try:
        logger.info("Searching inactive products in MongoDB")
        
        collection = _get_products_collection()
        
        cursor = collection.find(
            {
                "produto_inativo": {
                    "$regex": "^sim$",
                    "$options": "i",
                }
            },
            {
                "_id": 0,
                "codigo_produto": 1,
                "descricao_completa": 1,
                "familia_produto": 1,
                "unidade": 1,
                "preco_sintetico": 1,
            },
        ).limit(limit)
        
        records = list(cursor)
        
        logger.info(f"Found {len(records)} inactive MongoDB products")
        return records
    
    except Exception:
        logger.exception("Failed to get inactive products from MongoDB.")
        return []
    
def check_product_availability(
    tool_context: ToolContext,
    product_code: str,
    requested_quantity: int,
) -> dict:
    """
    Check wheter the requested quantity can be fulfilled with current stock
    """
    try:
        selected_products = tool_context.state.get("selected_products", [])
        
        if not product_code and selected_products:
            product_code = selected_products.get("codigo_produto", "")
            
        if not product_code:
            return {
                "disponivel": False,
                "message": "No product is currently selected for stock validation"
            }
        
        logger.info(f"Checking product availability for code = {product_code} | quantity = {requested_quantity}")
        
        inventory_service = InventoryService()
        stock_info = inventory_service.get_current_stock_by_product_code(product_code)
        
        if stock_info is None:
            result = {
                "codigo_produto": product_code,
                "disponivel": False,
                "message": "Product not found in stock database.",
            }
            tool_context.state["last_stock_check"] = {
                "product_code": product_code,
                "requested_quantity": requested_quantity,
                "stock_info": None,
                "result": result,
            }
            return result
            
        available_quantity = stock_info["quantidade"]
        is_available = available_quantity >= requested_quantity
        
        full_result = {
            "codigo_produto": stock_info["codigo_produto"],
            "descricao_completa": stock_info["descricao_completa"],
            "quantidade_solicitada": requested_quantity,
            "quantidade_disponivel": available_quantity,
            "estoque_minimo": stock_info["estoque_minimo"],
            "produto_inativo": stock_info["produto_inativo"],
            "disponivel": is_available,
            "em_estoque": stock_info["em_estoque"],
        }
        
        client_result = {
            "disponivel": is_available,
            "message": (
                "Requested quantity is available."
                if is_available
                else "Requested quantity is higher than current stock."
            ),
        }
        
        tool_context.state["last_stock_check"] = {
            "full_result": full_result,
            "client_result": client_result,
        }
        logger.info(f"Stock check completed for code = {product_code} | available = {is_available}")
        
        return client_result
    
    except Exception:
        logger.exception("Failed to check product availability")
        return {
            "codigo_produto": product_code,
            "disponivel": False,
            "message": "Failed to check product availability.",
        }
        
    
def get_stock_status_summary() -> dict:
    """
    Return a high-level stock status summary from MongoDB.
    """
    try:
        logger.info("Building stock status summary from MongoDB")
        
        inventory_service = InventoryService()
        summary = inventory_service.get_stock_status_summary()
        
        logger.info("Stock status summary built successfully")
        return summary
    
    except Exception:
        logger.exception("Failed to build stock status summary from MongoDB.")
        return {
            "total_produtos": 0,
            "produtos_em_falta": 0,
            "produtos_estoque_baixo": 0,
            "produtos_estoque_ok": 0,
        }
        
def get_out_stock_products(limit: int = 20) -> list[dict]:
    """
    Return products with zero stock from MongoDB
    """
    try:
        logger.info("Building out-of-stock products list from MongoDB")
        
        inventory_service = InventoryService()
        records = inventory_service.get_out_of_stock_products(limit=limit)
        
        logger.info("Out-of-stock products list built successfully")
        return records
    
    except Exception:
        logger.exception("Failed to get out-of-stock products from MongoDB.")
        return []
    
def get_negative_stock_products(limit: int = 20) -> list[dict]:
    """
    Return products with negative stock from MongoDB.
    """
    try:
        logger.info("Building negative-stock products list from MongoDB")
        
        inventory_service = InventoryService()
        records = inventory_service.get_negative_stock_products(limit=limit)
        
        logger.info("Negative-stock products list built successfully")
        return records
    
    except Exception:
        logger.exception("Failed to get negative-stock products from MongoDB.")
        return []
    
def get_low_stock_products(limit: int = 20) -> list[dict]:
    """
    Return products whose stock is below the configured minimum value.
    """
    try:
        logger.info("Searching low stock products in MongoDB")
        
        inventory_service = InventoryService()
        records = inventory_service.get_low_stock_products(limit=limit)
        
        logger.info(f"Found {len(records)} low stock MongoDB products")
        return records
    
    except Exception:
        logger.exception("Failed to get low stock products from MongoDB.")
        return []
    
def get_inventory_diff_by_period(
    reference_date: str,
    reference_period: str,
    limit: int = 20,
) -> list[dict]:
    """
    Return inventory diff records for a specific date and period
    """
    try:
        logger.info(f"Building inventory diff by period for date = {reference_date} | period = {reference_period}")
        
        inventory_service = InventoryService()
        records = inventory_service.get_inventory_diff_by_period(
            reference_date=reference_date,
            reference_period=reference_period,
            limit=limit,
        )
        
        logger.info("Inventory diff by period built successfully")
        return records
    
    except Exception:
        logger.exception("Failed to get inventory diff by period from MongoDB.")
        return []