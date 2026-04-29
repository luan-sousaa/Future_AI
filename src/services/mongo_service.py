from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from src.config.mongo_config import MongoConfig

class MongoService:
    def __init__(self, config: MongoConfig) -> None:
        self.config = config
        self.config.validate()
        
    def get_client(self) -> MongoClient:
        return MongoClient(self.config.mongo_uri)
    
    def get_database(self) -> Database:
        client = self.get_client()
        return client[self.config.db_name]
    
    def get_products_collection(self) -> Collection:
        db = self.get_database()
        return db[self.config.products_collection_name]
    
    def get_payments_collection(self) -> Collection:
        db = self.get_database()
        return db[self.config.payments_collection_name]
    
    def get_sales_history_collection(self) -> Collection:
        db = self.get_database()
        return db["sales_history"]
    
