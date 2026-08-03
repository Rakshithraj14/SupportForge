from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import get_settings
from app.telegram.commands import (
    help_command,
    incident_command,
    report_command,
    start_command,
)
from app.telegram.handlers import handle_document, handle_feedback, handle_text_message


def build_bot() -> Application:
    settings = get_settings()
    application = ApplicationBuilder().token(settings.telegram_bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("incident", incident_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(CallbackQueryHandler(handle_feedback, pattern=r"^feedback:"))

    return application


async def start_polling(application: Application) -> None:
    await application.initialize()
    await application.start()
    await application.updater.start_polling()


async def stop_polling(application: Application) -> None:
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
