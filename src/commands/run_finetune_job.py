"""
Script para executar fine-tuning do modelo de inventário
Uso: python -m src.commands.run_finetune_job
"""
import logging
import sys
import os
from dotenv import load_dotenv
from src.services.fine_tuning.finetune_openai import InventoryFineTuneJob

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Executa pipeline de fine-tuning"""
    try:
        # Recupera API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("❌ OPENAI_API_KEY não configurada no .env")
            sys.exit(1)

        logger.info("="*70)
        logger.info("🔧 CONFIGURAÇÃO")
        logger.info("="*70)
        logger.info(f"API Key: {api_key[:20]}...")
        logger.info(f"Modelo Base: gpt-3.5-turbo")
        logger.info("="*70)

        # Inicializa job
        job = InventoryFineTuneJob(api_key=api_key)

        # Executa pipeline
        result = job.run_full_pipeline(
            dataset_file="inventory_dataset.jsonl",
            model="gpt-4.1-mini",
            n_epochs=3,
            wait_for_completion=False  # ← Não espera (leva 1-2 horas)
        )

        # Salva log
        job.save_job_log()

        # Exibe resultado
        print("\n" + "="*70)
        print("📋 RESULTADO DO JOB")
        print("="*70)
        for key, value in result.items():
            print(f"{key:20s}: {value}")
        print("="*70)

        # Se criou job, mostre como verificar depois
        if "job_id" in result:
            print(f"\n💡 Para verificar status depois, use:")
            print(f"   python -m src.commands.check_finetune_status {result['job_id']}")

        return 0

    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())