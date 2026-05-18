import json
import logging
from datetime import datetime, timezone
from typing import Optional
import hashlib

from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

from src.config.mongo_config import MongoConfig
from src.services.mongo_service import MongoService

logger = logging.getLogger(__name__)

class InventoryFineTuneService:
    """
    Gerencia dataset de fine-tuning para o agente de inventário.
    Armazena exemplos no MongoDB e exporta em formato JSONL.
    """
    
    def __init__(self):
        """Inicializa com config e serviço MongoDB do projeto."""
        try:
            self.config = MongoConfig()
            self.mongo_service = MongoService(self.config)
            self.db = self.mongo_service.get_write_database()
            self.collection = self.db["finetune_inventory_examples"]
            self._setup_indexes()
            logger.info("InventoryFineTuneService inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar InventoryFineTuneService: {e}")
            raise

    def _setup_indexes(self):
        """Cria índices para otimizar consultas."""
        try:
            self.collection.create_index([("category", ASCENDING)])
            self.collection.create_index([("status", ASCENDING)])
            self.collection.create_index([("created_at", ASCENDING)])
            self.collection.create_index([("hash", ASCENDING)], unique=True)
            logger.info("Índices criados/verificados com sucesso")
        except Exception as e:
            logger.warning(f"Erro ao criar índices: {e}")
    
    def _generate_hash(self, messages: str) -> str:
        """Gera hash MD5 dos messages para detectar duplicatas."""
        content = json.dumps(messages, ensure_ascii=False, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
        
    def insert_examples(
        self,
        category: str,
        messages: list,
        source: str = "manual",
        model_version: str = "v1.0",
    ) -> Optional[str]:
        """Insere um exemplo no dataset"""
        try:
            doc = {
                "category": category,
                "messages": messages,
                "status": "pending_review",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "metadata": {
                    "source": source,
                    "language": "pt-BR",
                    "num_turns": len([m for m in messages if m["role"] != "system"]) // 2,
                    "model_version": model_version,
                },
                "hash": self._generate_hash(messages),
            }

            result = self.collection.insert_one(doc)
            logger.info(f"Exemplo inserido: {category} (ID: {result.inserted_id})")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.warning(f"Exemplo duplicado ignorado (categoria: {category})")
            return None
        except Exception as e:
            logger.error(f"Erro ao inserir exemplo: {e}")
            return None

    def insert_many_examples(self, examples: list) -> dict:
        """Insere múltiplos exemplos"""
        inserted = 0
        skipped = 0
        errors = 0
        
        for idx, example in enumerate(examples, 1):
            try:
                result = self.insert_examples(
                    category=example["category"],
                    messages=example["messages"],
                    source=example.get("source", "manual"),
                    model_version=example.get("model_version", "v1.0"),
                )
                if result:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"Erro ao inserir exemplo: {e}")
                errors += 1
        
        logger.info(f"Inserção concluída: {inserted} inseridos, {skipped} duplicados, {errors} erros")
        return {"inserted": inserted, "skipped": skipped, "errors": errors}
    
    def approve(self, example_id: str, reviewer: str = "system"):
        """Aprova um exemplo para fine-tuning"""
        try:
            self.collection.update_one(
                {"_id": ObjectId(example_id)},
                {
                    "$set": {
                        "status": "approved",
                        "updated_at": datetime.now(timezone.utc),
                        "reviewer": reviewer,
                    }
                },
            )
            logger.info(f"Exemplo aprovado: {example_id}")
        except Exception as e:
            logger.error(f"Erro ao aprovar exemplo: {e}")
    
    def reject(self, example_id: str, reason: str = ""):
        """Rejeita um exemplo."""
        try:
            self.collection.update_one(
                {"_id": ObjectId(example_id)},
                {
                    "$set": {
                        "status": "rejected",
                        "reject_reason": reason,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            logger.info(f"Exemplo rejeitado: {example_id} - {reason}")
        except Exception as e:
            logger.error(f"Erro ao rejeitar exemplo: {e}")
    
    def get_by_category(self, category: str, status: str = "approved") -> list:
        """Recupera exemplos por categoria"""
        try:
            return list(
                self.collection.find(
                    {"category": category, "status": status},
                    {"_id": 0, "messages": 1, "category": 1},
                )
            )
        
        except Exception:
            logger.exception(f"Erro ao recuperar exemplos por categoria: {category}")
            return []
        
    def get_pending_review(self) -> list:
        """Retorna exemplos aguardando revisão."""
        try:
            return list(
                self.collection.find(
                    {"status": "pending_review"},
                    {"_id": 1, "category": 1, "messages": 1},
                )
            )
        except Exception as e:
            logger.error(f"Erro ao recuperar exemplos pendentes: {e}")
            return []

    def approve_all_pending(self) -> int:
        """Aprova todos os exemplos pendentes."""
        try:
            result = self.collection.update_many(
                {"status": "pending_review"},
                {"$set": {"status": "approved", "updated_at": datetime.now(timezone.utc)}},
            )
            logger.info(f"Aprovados {result.modified_count} exemplos pendentes")
            return result.modified_count
        except Exception as e:
            logger.error(f"Erro ao aprovar pendentes: {e}")
            return 0

    def stats(self) -> dict:
        """Retorna estatísticas do dataset."""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": {"category": "$category", "status": "$status"},
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"_id.category": 1}},
            ]
            result = {}
            for doc in self.collection.aggregate(pipeline):
                cat = doc["_id"]["category"]
                st = doc["_id"]["status"]
                result.setdefault(cat, {})[st] = doc["count"]
            return result
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {}

    def export_jsonl(self, output_path: str, status: str = "approved") -> int:
        """Exporta dataset em formato JSONL para fine-tuning."""
        try:
            docs = self.collection.find({"status": status}, {"messages": 1, "_id": 0})
            count = 0
            with open(output_path, "w", encoding="utf-8") as f:
                for doc in docs:
                    f.write(
                        json.dumps({"messages": doc["messages"]}, ensure_ascii=False) + "\n"
                    )
                    count += 1
            logger.info(f"Exportados {count} exemplos → {output_path}")
            return count
        except Exception as e:
            logger.error(f"Erro ao exportar JSONL: {e}")
            return 0

    def clear_collection(self):
        """Limpa a coleção (uso com cuidado)."""
        try:
            result = self.collection.delete_many({})
            logger.warning(f"Coleção limpa: {result.deleted_count} documentos removidos")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Erro ao limpar coleção: {e}")
            return 0