from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PromptVersion

_SEED_DIR = Path(__file__).parent


def _read_seed(name: str) -> str:
    return (_SEED_DIR / f"{name}.md").read_text().strip()


async def get_active_prompt(db: AsyncSession, name: str = "support") -> PromptVersion:
    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.name == name, PromptVersion.active.is_(True))
        .order_by(PromptVersion.version.desc())
        .limit(1)
    )
    prompt_version = result.scalar_one_or_none()
    if prompt_version is None:
        prompt_version = PromptVersion(name=name, version=1, content=_read_seed(name), active=True)
        db.add(prompt_version)
        await db.commit()
        await db.refresh(prompt_version)
    return prompt_version


def build_user_prompt(question: str, context_chunks: list[str]) -> str:
    context_block = "\n\n".join(context_chunks) if context_chunks else "No relevant context found."
    return f"Context:\n{context_block}\n\nQuestion: {question}"
