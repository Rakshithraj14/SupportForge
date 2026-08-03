from sqlalchemy import select
from telegram import Update
from telegram.ext import ContextTypes

from app.config import get_settings
from app.database.models import Evaluation, Message
from app.database.session import AsyncSessionLocal


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


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = get_settings()
    chat_id = str(update.effective_chat.id)
    if settings.telegram_chat_id and chat_id != settings.telegram_chat_id:
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
