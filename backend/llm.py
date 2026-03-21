import json
import logging

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


async def call_gemini(prompt: str, api_key: str, model: str) -> dict:
    """Call Gemini and return parsed JSON. Retries once on malformed JSON."""
    url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.7,
        },
    }

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            if attempt == 0:
                logger.warning("Gemini returned invalid JSON, retrying: %s", exc)
                continue
            logger.error("Gemini returned invalid JSON twice: %s", exc)
            raise HTTPException(502, "AI returned invalid response") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("Gemini API error: %s", exc)
            raise HTTPException(502, "AI service temporarily unavailable") from exc
        except httpx.RequestError as exc:
            logger.error("Gemini network error: %s", exc)
            raise HTTPException(502, "AI service temporarily unavailable") from exc

    raise HTTPException(502, "AI returned invalid response")
