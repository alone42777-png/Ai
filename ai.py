import httpx
from fastapi import HTTPException
from app.config import settings

async def chat_completion(payload: dict) -> dict:
    url = settings.ai_base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {settings.ai_api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(502, f"AI provider returned HTTP {exc.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(502, "Could not connect to AI provider")
