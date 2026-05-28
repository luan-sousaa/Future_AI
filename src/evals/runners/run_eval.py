import logging
import uuid

from datetime import datetime

from src.agent.inventory_agent import root_agent

from src.evals.engine.evaluation_engine import (
    EvaluationEngine,
)

from src.evals.datasets.load_dataset import (
    load_eval_dataset,
)

from src.evals.schemas.trace import (
    ExecutionTrace,
    TraceEvent,
)

from src.evals.traces.trace_store import TraceStore


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger("inventory_eval")


DATASET_PATH = (
    "src/datasets/inventory_dataset.jsonl"
)


def extract_last_user_message(messages):
    users = [
        m
        for m in messages
        if m.role == "user"
    ]

    return users[-1].content


def run():

    logger.info("Carregando dataset...")

    dataset = load_eval_dataset(DATASET_PATH)

    logger.info(
        "Dataset carregado | total_cases=%s",
        len(dataset),
    )

    engine = EvaluationEngine()

    trace_store = TraceStore()

    results = []

    for index, case in enumerate(dataset):

        logger.info(
            "Executando case | %s/%s | case_id=%s",
            index + 1,
            len(dataset),
            case.id,
        )

        user_message = extract_last_user_message(
            case.messages
        )

        trace = ExecutionTrace(
            trace_id=f"trace_{uuid.uuid4().hex[:8]}",
            created_at=datetime.now().isoformat(),
            events=[],
        )

        trace.events.append(
            TraceEvent(
                timestamp=datetime.now().isoformat(),
                type="user_message",
                payload={
                    "message": user_message,
                },
            )
        )

        logger.info(
            "Invocando agente | input=%s",
            user_message,
        )

        response = root_agent.run(user_message)

        response_text = str(response)

        logger.info(
            "Resposta recebida | chars=%s",
            len(response_text),
        )

        trace.events.append(
            TraceEvent(
                timestamp=datetime.now().isoformat(),
                type="assistant_response",
                payload={
                    "response": response_text,
                },
            )
        )

        tools_used = []

        if hasattr(response, "tool_calls"):
            tools_used = [
                tool.name
                for tool in response.tool_calls
            ]

        logger.info(
            "Tools utilizadas | %s",
            tools_used,
        )

        result = engine.evaluate(
            case=case,
            response=response_text,
            tools_used=tools_used,
        )

        results.append(result)

        trace_store.save(trace)

        logger.info(
            "Resultado | passed=%s",
            result.passed,
        )

        for metric in result.metrics:

            logger.info(
                "Metric | %s | passed=%s | score=%s",
                metric.metric_name,
                metric.passed,
                metric.score,
            )

    total = len(results)

    passed = sum(r.passed for r in results)

    logger.info("=" * 60)

    logger.info(
        "FINAL RESULT | total=%s | passed=%s | rate=%.2f%%",
        total,
        passed,
        (passed / total) * 100,
    )

    logger.info("=" * 60)


if __name__ == "__main__":
    run()
