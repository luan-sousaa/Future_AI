import os
from dotenv import load_dotenv

load_dotenv()

class MongoConfig:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGO_DB_NAME")
        self.collection_name = os.getenv("MONGO_COLLECTION_NAME")
    
    def validate(self) -> None:
        if not self.mongo_uri:
            raise ValueError("MONGO_URI is not configured.")

