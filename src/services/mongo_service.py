from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from src.config.mongo_config import MongoConfig

class MongoService:
    def __init__(self, config: MongoConfig) -> None:
        self.config = config
        
    def get_read_client(self) -> MongoClient:
        self.config.validate_read()
        return MongoClient(self.config.mongo_read_uri)
    
    def get_write_client(self) -> MongoClient:
        self.config.validate_write()
        return MongoClient(self.config.mongo_write_uri)
    
    def get_read_database(self) -> Database:
        client = self.get_read_client()
        return client[self.config.db_name]
    
    def get_write_database(self) -> Database:
        client = self.get_write_client()
        return client[self.config.db_name]
    
    def get_products_collection(self, read_only: bool = True) -> Collection:
        db = self.get_read_database() if read_only else self.get_write_database()
        return db[self.config.products_collection_name]
    
    def get_payments_collection(self, read_only: bool = True) -> Collection:
        db = self.get_read_database() if read_only else self.get_write_database()
        return db[self.config.payments_collection_name]
    
    def get_sales_history_collection(self, read_only: bool = True) -> Collection:
        db = self.get_read_database() if read_only else self.get_write_database()
        return db[self.config.sales_history_collecttion_name]
    
    def get_inventory_snapshots_collection(self, read_only: bool = True) -> Collection:
        db = self.get_read_database() if read_only else self.get_write_database()
        return db[self.config.inventory_snapshots_collection_name]
    
    def get_inventory_diff_collection(self, read_only: bool = True) -> Collection:
        db = self.get_read_database() if read_only else self.get_write_database()
        return db[self.config.inventory_diff_collection_name]
    
