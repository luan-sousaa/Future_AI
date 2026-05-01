import logging
from typing import Optional 

from google.adk.tools import ToolContext

from src.config.mongo_config import MongoConfig
from src.services.mongo_service import MongoService

logger = logging.getLogger(__name__)

# Helpers
def _get_products_collection():
    config = MongoConfig()
    mongo_service = MongoService(config)
    return mongo_service.get_products_collection()

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
        
        records = list(cursor)
        
        tool_context.state["last_search_term"] = term
        tool_context.state["last_search_results"] = records
        
        logger.info(f"Found {len(records)} matching MongoDB products")
        return records
    
    except Exception:
        logger.exception("Failed to search products by name in MongoDB")
        return []
    
def get_product_by_code(
    tool_context: ToolContext,
    product_code: str,
) -> Optional[str]:
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

        logger.info(f"Total selected products: {len(selected_products)}")
        return produto

    except Exception:
        logger.exception("Failed to select product by code from MongoDB")
        return None
    
def get_product_stock_and_price_summary(
    tool_context: ToolContext,
    product_code: str = "",
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
        
        summaries: list[dict] = []
        
        for code in selected_codes:
            produto = _get_product_by_code(code)
            if produto is None:
                logger.warning(f"Skipping missing product code during summary: {code}")
                
            resumo = {
                "codigo_produto": produto["codigo_produto"],
                "descricao_completa": produto["descricao_completa"],
                "familia_produto": produto.get("familia_produto"),
                "unidade": produto.get("unidade"),
                "produto_inativo": produto.get("produto_inativo"),
                "quantidade_em_estoque": produto.get("quantidade"),
                "estoque_minimo": produto.get("estoque_minimo"),
                "preco_sintetico": produto.get("preco_sintetico"),
            }
            
            summaries.append(resumo)
        
        tool_context.state["last_products_summary"] = summaries
        
        logger.info(f"Built summaries for {len(summaries)} MongoD products")
        return summaries
    
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
    
