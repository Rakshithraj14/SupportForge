import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api import chat, health, knowledge
from app.database.session import Base, engine
from app.monitoring.prometheus import HTTP_REQUEST_LATENCY
from app.monitoring.prometheus import router as metrics_router
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


@app.middleware("http")
async def track_request_latency(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    HTTP_REQUEST_LATENCY.labels(
        method=request.method, path=request.url.path, status_code=response.status_code
    ).observe(duration)
    return response


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(metrics_router)
