"""
Job de Fine-tuning para modelo de inventário
Exporta dataset → Upload → Cria job → Monitora treinamento
"""
import json
import logging
import time
from datetime import datetime
from typing import Optional
from openai import OpenAI
from src.services.fine_tune import InventoryFineTuneService

logger = logging.getLogger(__name__)


class InventoryFineTuneJob:
    """Gerencia job de fine-tuning do modelo de inventário"""

    def __init__(self, api_key: Optional[str] = None):
        """Inicializa cliente OpenAI"""
        self.client = OpenAI(api_key=api_key)
        self.fine_tune_service = InventoryFineTuneService()
        self.job_log = {}

    def validate_jsonl_file(self, filepath: str) -> bool:
        """Valida se arquivo JSONL está correto"""
        try:
            line_count = 0
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "messages" not in data:
                            logger.error(f"Linha {line_count} sem 'messages'")
                            return False
                        line_count += 1

            logger.info(f"✅ Arquivo válido: {line_count} exemplos")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao validar JSONL: {e}")
            return False

    def upload_training_file(self, filepath: str = "inventory_finetune_dataset.jsonl") -> str:
        """
        Faz upload do arquivo JSONL para OpenAI
        Retorna file_id
        """
        try:
            logger.info(f"📤 Uploadando {filepath}...")

            if not self.validate_jsonl_file(filepath):
                raise ValueError("Arquivo JSONL inválido")

            with open(filepath, "rb") as f:
                response = self.client.files.create(
                    file=f,
                    purpose="fine-tune"
                )

            file_id = response.id
            logger.info(f"✅ Upload concluído: {file_id}")
            self.job_log["file_id"] = file_id
            self.job_log["upload_time"] = datetime.now().isoformat()

            return file_id

        except Exception as e:
            logger.error(f"❌ Erro no upload: {e}")
            raise

    def create_fine_tune_job(
        self,
        file_id: str,
        model: str = "gpt-4-mini",
        n_epochs: int = 3,
        learning_rate_multiplier: float = 1.0,
    ) -> str:
        """
        Cria job de fine-tuning
        Retorna job_id
        """
        try:
            logger.info(f"🚀 Criando job de fine-tuning...")
            logger.info(f"   Modelo: {model}")
            logger.info(f"   Épocas: {n_epochs}")
            logger.info(f"   Learning Rate: {learning_rate_multiplier}")

            job = self.client.fine_tuning.jobs.create(
                training_file=file_id,
                model=model,
                hyperparameters={
                    "n_epochs": n_epochs,
                    "learning_rate_multiplier": learning_rate_multiplier,
                },
            )

            job_id = job.id
            logger.info(f"✅ Job criado: {job_id}")
            self.job_log["job_id"] = job_id
            self.job_log["model"] = model
            self.job_log["status"] = job.status
            self.job_log["creation_time"] = datetime.now().isoformat()

            return job_id

        except Exception as e:
            logger.error(f"❌ Erro ao criar job: {e}")
            raise

    def check_job_status(self, job_id: str) -> dict:
        """Verifica status atual do job"""
        try:
            job = self.client.fine_tuning.jobs.retrieve(job_id)

            status_info = {
                "job_id": job.id,
                "status": job.status,
                "model": job.model,
                "training_file": job.training_file,
                "fine_tuned_model": job.fine_tuned_model or "Em treinamento...",
                "created_at": str(job.created_at),
            }

            logger.info(f"📊 Status do Job {job_id}:")
            logger.info(f"   Status: {job.status}")
            logger.info(f"   Modelo Base: {job.model}")
            logger.info(f"   Modelo Treinado: {job.fine_tuned_model or 'Aguardando...'}")

            self.job_log["status"] = job.status
            if job.fine_tuned_model:
                self.job_log["fine_tuned_model"] = job.fine_tuned_model

            return status_info

        except Exception as e:
            logger.error(f"❌ Erro ao verificar status: {e}")
            raise

    def wait_for_job(
        self, job_id: str, max_wait_minutes: int = 120, check_interval: int = 30
    ) -> str:
        """
        Aguarda conclusão do job
        Retorna model_id do modelo treinado
        """
        logger.info(f"⏳ Aguardando conclusão do job... (máx {max_wait_minutes} minutos)")

        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60

        while True:
            elapsed = time.time() - start_time

            if elapsed > max_wait_seconds:
                logger.error(f"❌ Timeout: job não completou em {max_wait_minutes} minutos")
                raise TimeoutError(f"Job excedeu tempo limite de {max_wait_minutes} minutos")

            job = self.client.fine_tuning.jobs.retrieve(job_id)

            status = job.status
            logger.info(f"[{elapsed//60:.0f}min] Status: {status}")

            if status == "succeeded":
                model_id = job.fine_tuned_model
                logger.info(f"✅ Job concluído! Modelo: {model_id}")
                self.job_log["fine_tuned_model"] = model_id
                self.job_log["status"] = "succeeded"
                return model_id

            elif status == "failed":
                logger.error(f"❌ Job falhou!")
                raise RuntimeError("Job de fine-tuning falhou")

            elif status == "cancelled":
                logger.error(f"❌ Job foi cancelado!")
                raise RuntimeError("Job de fine-tuning foi cancelado")

            # Aguarda antes de próxima verificação
            logger.info(f"   Próxima verificação em {check_interval}s...")
            time.sleep(check_interval)

    def run_full_pipeline(
        self,
        dataset_file: str = "inventory_finetune_dataset.jsonl",
        model: str = "gpt-4-mini",
        n_epochs: int = 3,
        wait_for_completion: bool = False,
    ) -> dict:
        """
        Executa pipeline completo:
        Export → Upload → Job Creation → Wait (optional)
        """
        try:
            logger.info("="*70)
            logger.info("🚀 INICIANDO PIPELINE DE FINE-TUNING")
            logger.info("="*70)

            # 1. Export do dataset
            logger.info("\n1️⃣  Exportando dataset...")
            count = self.fine_tune_service.export_jsonl(dataset_file, status="approved")
            logger.info(f"   ✅ {count} exemplos exportados")

            # 2. Upload
            logger.info("\n2️⃣  Fazendo upload...")
            file_id = self.upload_training_file(dataset_file)

            # 3. Criar job
            logger.info("\n3️⃣  Criando job de fine-tuning...")
            job_id = self.create_fine_tune_job(
                file_id=file_id,
                model=model,
                n_epochs=n_epochs,
            )

            self.job_log["pipeline_status"] = "job_created"

            # 4. Aguardar (opcional)
            if wait_for_completion:
                logger.info("\n4️⃣  Aguardando conclusão...")
                model_id = self.wait_for_job(job_id)
                self.job_log["final_model"] = model_id
            else:
                logger.info(f"\n4️⃣  Job criado. Você pode verificar depois com job_id: {job_id}")
                self.job_log["final_model"] = f"Aguardando (job: {job_id})"

            logger.info("\n" + "="*70)
            logger.info("✅ PIPELINE CONCLUÍDO")
            logger.info("="*70)

            return self.job_log

        except Exception as e:
            logger.error(f"❌ Erro no pipeline: {e}")
            self.job_log["error"] = str(e)
            self.job_log["pipeline_status"] = "failed"
            raise

    def save_job_log(self, filepath: str = "finetune_job_log.json"):
        """Salva log do job para referência"""
        try:
            with open(filepath, "w") as f:
                json.dump(self.job_log, f, indent=2, default=str)
            logger.info(f"💾 Log salvo em: {filepath}")
        except Exception as e:
            logger.error(f"Erro ao salvar log: {e}")

    def get_fine_tuned_model_id(self, job_id: str) -> Optional[str]:
        """Recupera model_id de um job existente"""
        try:
            job = self.client.fine_tuning.jobs.retrieve(job_id)
            return job.fine_tuned_model
        except Exception as e:
            logger.error(f"Erro ao recuperar model_id: {e}")
            return None