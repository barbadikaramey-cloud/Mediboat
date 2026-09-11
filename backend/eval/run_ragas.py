"""RAGAS evaluation runner.

Run after ingestion is complete and the backend is configured:
    uv run python -m eval.run_ragas

Evaluates faithfulness and context precision on the eval_set.json Q&A pairs.
Results are logged to stdout and saved to eval/results/ragas_results.json.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

EVAL_DIR = Path(__file__).parent
RESULTS_DIR = EVAL_DIR / "results"
EVAL_SET_PATH = EVAL_DIR / "eval_set.json"


async def evaluate():
    """Run RAGAS evaluation against the live RAG pipeline."""
    from ragas import evaluate as ragas_evaluate
    from ragas.metrics import faithfulness, context_precision, answer_relevancy
    from datasets import Dataset

    # Import graph after setting up env
    from app.graph import run_chat

    with open(EVAL_SET_PATH) as f:
        eval_set = json.load(f)

    # Skip SQL-only questions for RAG eval (they don't return chunks)
    doc_questions = [q for q in eval_set if not q.get("is_sql")]

    logger.info("Running RAGAS eval on %d document questions", len(doc_questions))

    questions, answers, contexts, ground_truths = [], [], [], []

    for item in doc_questions:
        role = item["role"]
        question = item["question"]
        gt = item["ground_truth"]

        logger.info("Evaluating: [%s] %s", role, question[:60])
        result = await run_chat(question=question, role=role, username=f"eval_{role}")

        answer = result.get("answer", "")
        # Build context from source citations (sources contain doc+section references)
        # For RAGAS we need the actual chunk texts — re-run retrieval to get them
        from app.retrieval.hybrid_search import hybrid_search
        from app.retrieval.rerank import rerank
        chunks = hybrid_search(query=question, role=role, top_k=10)
        top_chunks = rerank(query=question, chunks=chunks)
        context_texts = [c.text for c in top_chunks]

        questions.append(question)
        answers.append(answer)
        contexts.append(context_texts)
        ground_truths.append(gt)

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    result = ragas_evaluate(
        dataset=dataset,
        metrics=[faithfulness, context_precision, answer_relevancy],
    )

    logger.info("\n=== RAGAS Results ===")
    result_dict = result.to_pandas().to_dict(orient="records")
    for row in result_dict:
        logger.info("  Q: %s", row.get("question", "")[:60])
        logger.info("    Faithfulness: %.3f", row.get("faithfulness", 0))
        logger.info("    Context Precision: %.3f", row.get("context_precision", 0))
        logger.info("    Answer Relevancy: %.3f", row.get("answer_relevancy", 0))

    # Aggregate scores
    df = result.to_pandas()
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "num_questions": len(doc_questions),
        "faithfulness_mean": float(df["faithfulness"].mean()),
        "context_precision_mean": float(df["context_precision"].mean()),
        "answer_relevancy_mean": float(df["answer_relevancy"].mean()),
        "per_question": result_dict,
    }
    logger.info("\n=== Aggregate ===")
    logger.info("  Faithfulness:       %.3f", summary["faithfulness_mean"])
    logger.info("  Context Precision:  %.3f", summary["context_precision_mean"])
    logger.info("  Answer Relevancy:   %.3f", summary["answer_relevancy_mean"])

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / "ragas_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info("Results saved to %s", out_path)


if __name__ == "__main__":
    asyncio.run(evaluate())
