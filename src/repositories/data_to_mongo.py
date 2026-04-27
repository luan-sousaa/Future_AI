import logging
import os
 
import pandas as pd  
from dotenv import load_dotenv

from src.config.mongo_config import MongoConfig
from src.services.mongo_service import MongoService
from src.tools.db_tools_excel import load_excel_data

logger = logging.getLogger(__name__)

def import_products_to_mongo() -> None:
    df = load_excel_data()
    if df is None:
        logger.warning("Failed to load Excel data. Aborting import.")
        return
    
    config = MongoConfig()
    mongo_service =MongoService(config)
    collection = mongo_service.get_products_collection()
    
    collection.create_index("codigo_produto", unique=True)
    
    inserted_count = 0
    updated_count = 0
    unchanged_count = 0
    
    for row in df.to_dict(orient="records"):
        doc = {
            key: (None if pd.isna(value) else value)
            for key, value in row.items()
        }
        
        result = collection.update_one(
            {"codigo_produto": doc["codigo_produto"]},
            {"$set": doc},
            upsert=True,
        )
        
        if result.upserted_id is not None:
            inserted_count += 1
        elif result.modified_count > 0:
            updated_count += 1
        else:
            unchanged_count += 1
        
    logger.info(f"Mongo import completed. Inserted: {inserted_count} | Updated: {updated_count} | Unchanged: {unchanged_count}")
    
    
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s"
    )
    import_products_to_mongo()