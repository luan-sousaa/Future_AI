"""
Verifica status de um job de fine-tuning
Uso: python -m src.commands.check_finetune_status <job_id>
"""
import sys
import os
import logging
from dotenv import load_dotenv
from src.services.fine_tuning.finetune_openai import InventoryFineTuneJob

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python -m src.commands.check_finetune_status <job_id>")
        print("\nExemplo:")
        print("   python -m src.commands.check_finetune_status ftjob-abc123xyz")
        print("\n💡 Dica: O job_id foi exibido ao executar run_finetune.py")
        sys.exit(1)

    job_id = sys.argv[1]
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.error("❌ OPENAI_API_KEY não configurada")
        sys.exit(1)

    logger.info(f"Verificando status do job: {job_id}")

    job = InventoryFineTuneJob(api_key=api_key)
    status = job.check_job_status(job_id)

    print("\n" + "="*70)
    print("📊 STATUS DO JOB")
    print("="*70)
    for key, value in status.items():
        print(f"{key:20s}: {value}")
    print("="*70)

    # Se concluído, mostre como usar
    if status["status"] == "succeeded":
        print(f"\n✅ Modelo pronto para uso!")
        print(f"\nModel ID: {status['fine_tuned_model']}")
        print(f"\nAtualize seu .env:")
        print(f'   OPENAI_MODEL_FINETUNED="{status["fine_tuned_model"]}"')

    elif status["status"] == "running":
        print(f"\n⏳ Job ainda está em treinamento...")
        print(f"   Verifique novamente em alguns minutos")

    elif status["status"] in ["failed", "cancelled"]:
        print(f"\n❌ Job não completou com sucesso")
        print(f"   Status: {status['status']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
