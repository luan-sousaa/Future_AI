import os
from dotenv import load_dotenv

load_dotenv()

class MongoConfig:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGO_DB_NAME")
        self.products_collection_name = os.getenv("MONGO_PRODUCTS_COLLECTION")
        self.payments_collection_name = os.getenv("MONGO_PAYMENTS_COLLECTION")
        self.sales_history_collecttion_name = os.getenv("MONGO_SALES_HISTORY_COLLECTION")
        self.inventory_snapshots_collection_name = os.getenv("MONGO_INVENTORY_SNAPSHOTS_COLLECTION")
        self.inventory_diff_collection_name = os.getenv("MONGO_INVENTORY_DIFF_COLLECTION")
    
    def validate(self) -> None:
        if not self.mongo_uri:
            raise ValueError("MONGO_URI is not configured.")
        if not self.db_name:
            raise ValueError("MONGO_DB_NAME is not configured.")
        if not self.products_collection_name:
            raise ValueError("MONGO_COLLECTION_NAME is not configured.")
        if not self.payments_collection_name:
            raise ValueError("MONGO_PAYMENTS_COLLECTION is not configured.")

