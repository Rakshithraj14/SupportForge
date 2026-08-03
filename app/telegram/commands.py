import asyncio

from sqlalchemy import select
from telegram import Update
from telegram.ext import ContextTypes

from app.config import get_settings
from app.database.models import Evaluation, Message
from app.database.session import AsyncSessionLocal
from app.simulator.incidents import INCIDENTS, run_incident_simulation
from app.simulator.personas import PERSONAS
from app.workers.evaluation import evaluate_message_task


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to SupportForge! Ask me a question, or send a PDF/Markdown "
        "file to add it to the knowledge base."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Just send a message to ask a question.\n"
        "Send a .pdf or .md file to add it to the knowledge base.\n"
        "Use 👍/👎 under an answer to give feedback."
    )


def _authorized(update: Update) -> bool:
    settings = get_settings()
    chat_id = str(update.effective_chat.id)
    return not settings.telegram_chat_id or chat_id == settings.telegram_chat_id


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        await update.message.reply_text("You're not authorized to use this command.")
        return

    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(Message, Evaluation)
                .join(Evaluation, Evaluation.message_id == Message.id)
                .order_by(Evaluation.faithfulness.asc())
                .limit(5)
            )
        ).all()

    if not rows:
        await update.message.reply_text("No flagged answers evaluated yet.")
        return

    lines = ["Worst-scoring flagged answers:"]
    for message, evaluation in rows:
        lines.append(
            f"\n#{message.id}: {message.content[:100]}\n"
            f"faithfulness={evaluation.faithfulness:.2f} "
            f"hallucination={evaluation.hallucination:.2f} "
            f"context_precision={evaluation.context_precision:.2f} "
            f"context_recall={evaluation.context_recall:.2f}"
        )
    await update.message.reply_text("\n".join(lines))


async def _wait_for_evaluations(message_ids: list[int], timeout: int = 900) -> dict[int, Evaluation]:
    deadline = asyncio.get_event_loop().time() + timeout
    remaining = set(message_ids)
    found: dict[int, Evaluation] = {}

    while remaining and asyncio.get_event_loop().time() < deadline:
        async with AsyncSessionLocal() as db:
            rows = (
                await db.execute(select(Evaluation).where(Evaluation.message_id.in_(remaining)))
            ).scalars().all()
        for row in rows:
            found[row.message_id] = row
            remaining.discard(row.message_id)
        if remaining:
            await asyncio.sleep(5)

    return found


async def incident_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        await update.message.reply_text("You're not authorized to use this command.")
        return

    if not context.args or context.args[0] not in INCIDENTS:
        await update.message.reply_text(
            "Usage: /incident <name>\nAvailable: " + ", ".join(INCIDENTS)
        )
        return

    incident_name = context.args[0]
    await update.message.reply_text(
        f"Simulating incident '{incident_name}' across {len(PERSONAS)} personas..."
    )

    results = await run_incident_simulation(incident_name)
    for result in results:
        evaluate_message_task.delay(result["message_id"])

    await update.message.reply_text("Generated, now evaluating responses (a few minutes)...")

    message_ids = [r["message_id"] for r in results]
    evaluations = await _wait_for_evaluations(message_ids)

    if not evaluations:
        await update.message.reply_text("Evaluation timed out — check /report later.")
        return

    metrics = ("faithfulness", "hallucination", "context_precision", "context_recall")
    avg = {m: sum(getattr(e, m) for e in evaluations.values()) / len(evaluations) for m in metrics}

    worst_id = min(evaluations, key=lambda mid: evaluations[mid].faithfulness)
    worst_result = next(r for r in results if r["message_id"] == worst_id)

    lines = [
        f"Incident report: {incident_name}",
        f"{len(evaluations)}/{len(results)} evaluated\n",
        f"avg faithfulness={avg['faithfulness']:.2f} hallucination={avg['hallucination']:.2f} "
        f"context_precision={avg['context_precision']:.2f} context_recall={avg['context_recall']:.2f}",
        f"\nWorst-scoring ({worst_result['persona']}): {worst_result['answer'][:150]}",
    ]
    await update.message.reply_text("\n".join(lines))
