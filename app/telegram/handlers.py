from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.database.models import Feedback
from app.database.session import AsyncSessionLocal
from app.evaluation.evaluator import evaluate_message
from app.services.chat_service import handle_chat_message
from app.services.knowledge_service import ingest_document


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    question = update.message.text

    async with AsyncSessionLocal() as db:
        message = await handle_chat_message(db, chat_id=chat_id, question=question)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👍", callback_data=f"feedback:{message.id}:up"),
                InlineKeyboardButton("👎", callback_data=f"feedback:{message.id}:down"),
            ]
        ]
    )
    await update.message.reply_text(message.content, reply_markup=keyboard)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_file = await update.message.document.get_file()
    content = bytes(await telegram_file.download_as_bytearray())
    filename = update.message.document.file_name
    content_type = update.message.document.mime_type or "application/octet-stream"

    async with AsyncSessionLocal() as db:
        document = await ingest_document(
            db, filename=filename, content_type=content_type, content=content
        )

    await update.message.reply_text(
        f"Indexed '{document.filename}' into {document.chunk_count} chunks."
    )


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, message_id, vote = query.data.split(":")
    message_id = int(message_id)
    is_positive = vote == "up"

    async with AsyncSessionLocal() as db:
        db.add(Feedback(message_id=message_id, is_positive=is_positive))
        await db.commit()

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text("Thanks for your feedback!")

    if not is_positive:
        async with AsyncSessionLocal() as db:
            await evaluate_message(db, message_id)
