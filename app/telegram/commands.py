from telegram import Update
from telegram.ext import ContextTypes


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
