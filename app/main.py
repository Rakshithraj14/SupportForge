from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import chat, health, knowledge
from app.database.session import Base, engine
from app.telegram.bot import build_bot, start_polling, stop_polling


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot = build_bot()
    await start_polling(bot)
    try:
        yield
    finally:
        await stop_polling(bot)


app = FastAPI(title="SupportForge", lifespan=lifespan)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(knowledge.router)
