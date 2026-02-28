import asyncio
from typing import Any


async def _fetch_remote_profile(user_id: str) -> dict[str, Any]:
    await asyncio.sleep(0)
    return {"user_id": user_id, "status": "ok"}


async def fetch_user_profile(user_id: str) -> dict[str, Any]:
    return await asyncio.to_thread(asyncio.run, _fetch_remote_profile(user_id))
