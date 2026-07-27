from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import chat, health, knowledge
from app.database.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="SupportForge", lifespan=lifespan)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(knowledge.router)
