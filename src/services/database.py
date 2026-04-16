import json
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "repositories" / "price_table.json"

def _load_json():
    """
    Helper de carregamento do banco mockado
    """
    with DB_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)
    
