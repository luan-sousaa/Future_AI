"""
Script para popular o banco de fine-tuning do agente de inventário.

Uso: python -m src.commands.populate_finetune
"""

import os
import sys
import logging
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

from src.services.fine_tuning.fine_tune import InventoryFineTuneService
from src.repositories.inventory_finetune_examples import (
    INVENTORY_FINETUNE_EXAMPLES,
    RECOMMENDED_QUANTITIES,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def print_header(title: str):
    """Imprime um header formatado."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_recommendations():
    """Exibe quantidades recomendadas de exemplos."""
    print_header("📊 QUANTIDADE RECOMENDADA DE EXEMPLOS POR CATEGORIA")

    total_min, total_ideal = 0, 0
    for cat, info in RECOMMENDED_QUANTITIES.items():
        print(f"\n  🏷️  {cat}")
        print(f"     Mínimo : {info['min']:>4} exemplos")
        print(f"     Ideal  : {info['ideal']:>4} exemplos")
        total_min += info["min"]
        total_ideal += info["ideal"]

    print("\n" + "-" * 70)
    print(f"  TOTAL MÍNIMO : {total_min:>5} exemplos")
    print(f"  TOTAL IDEAL  : {total_ideal:>5} exemplos")
    print("=" * 70)


def run_populate():
    """Popula o banco de fine-tuning com exemplos."""
    print_recommendations()

    try:
        print_header("🚀 INICIALIZANDO SERVIÇO DE FINE-TUNING")
        service = InventoryFineTuneService()
        print("  ✅ Conexão com MongoDB estabelecida")

    except Exception as e:
        logger.error(f"Erro ao conectar ao MongoDB: {e}")
        print(f"  ❌ Erro: {e}")
        return False

    try:
        print_header("📥 INSERINDO EXEMPLOS DE FINE-TUNING")
        print(f"  Total de exemplos a inserir: {len(INVENTORY_FINETUNE_EXAMPLES)}")

        result = service.insert_many_examples(INVENTORY_FINETUNE_EXAMPLES)
        print(f"\n  ✅ Inseridos: {result['inserted']}")
        print(f"  ⚠️  Ignorados (duplicatas): {result['skipped']}")
        if result["errors"] > 0:
            print(f"  ❌ Erros: {result['errors']}")

    except Exception as e:
        logger.error(f"Erro ao inserir exemplos: {e}")
        print(f"  ❌ Erro: {e}")
        return False

    try:
        print_header("🔍 APROVANDO EXEMPLOS PENDENTES")
        approved_count = service.approve_all_pending()
        print(f"  ✅ {approved_count} exemplos aprovados")

    except Exception as e:
        logger.error(f"Erro ao aprovar exemplos: {e}")
        print(f"  ❌ Erro: {e}")
        return False

    try:
        print_header("📈 ESTATÍSTICAS DO DATASET")
        stats = service.stats()

        if not stats:
            print("  ⚠️  Nenhum dado para exibir")
        else:
            total_geral = 0
            for category in sorted(stats.keys()):
                counts = stats[category]
                total = sum(counts.values())
                total_geral += total
                status_str = " | ".join(f"{st}: {c}" for st, c in sorted(counts.items()))
                print(f"  {category:<30} → {total:>3} exemplo(s) | {status_str}")

            print("\n" + "-" * 70)
            print(f"  TOTAL GERAL : {total_geral:>5} exemplos")

    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        print(f"  ❌ Erro: {e}")
        return False

    try:
        print_header("💾 EXPORTANDO DATASET JSONL")
        output_file = "inventory_finetune_dataset.jsonl"
        count = service.export_jsonl(output_file, status="approved")
        print(f"  ✅ {count} exemplos exportados")
        print(f"  📁 Arquivo: {output_file}")

    except Exception as e:
        logger.error(f"Erro ao exportar JSONL: {e}")
        print(f"  ❌ Erro: {e}")
        return False

    print_header("🎉 POPULAÇÃO DO DATASET CONCLUÍDA COM SUCESSO!")
    print("\n  Próximos passos:")
    print("  1. Revisar o arquivo JSONL exportado")
    print("  2. Usar o dataset para fine-tuning do modelo")
    print("  3. Monitorar performance do modelo treinado\n")

    return True


if __name__ == "__main__":
    success = run_populate()
    sys.exit(0 if success else 1)