import argparse
import asyncio

from app.database.session import AsyncSessionLocal
from app.llm.prompts import _read_seed, set_active_prompt


async def main(name: str) -> None:
    content = _read_seed(name)
    async with AsyncSessionLocal() as db:
        prompt_version = await set_active_prompt(db, content, name=name)
    print(f"Activated {name} v{prompt_version.version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Promote a seed prompt file to a new active version.")
    parser.add_argument("name", nargs="?", default="support")
    args = parser.parse_args()
    asyncio.run(main(args.name))
