#!/usr/bin/env python3
"""
tts_function.py — Yandex Cloud Function для синтеза речи через edge-tts

Зависимости (requirements-tts.txt):
  edge-tts>=6.0.0

Запрос:
  POST {"texts": ["текст1", "текст2"], "voice": "ru-RU-DmitryNeural", "pitch": "-10Hz"}
Ответ:
  {"audios": {"текст1": "<base64>", "текст2": "<base64>"}, "format": "mp3"}
"""

import asyncio
import json
import base64

try:
    import edge_tts
except ImportError:
    edge_tts = None

VOICE = "ru-RU-DmitryNeural"
PITCH = "-10Hz"
VOLUME = "+30%"


def _cors(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body, ensure_ascii=False) if isinstance(body, (dict, list)) else str(body),
    }


async def _synthesize_one(text, voice, pitch, volume):
    result = b""
    communicate = edge_tts.Communicate(text, voice=voice, pitch=pitch, volume=volume)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            result += chunk["data"]
    return text, result


def handler(event, context):
    try:
        if event.get("httpMethod") == "OPTIONS":
            return _cors(200, {"ok": True})

        if edge_tts is None:
            return _cors(500, {"error": "edge-tts not installed"})

        body = json.loads(event.get("body", "{}"))
        voice = body.get("voice", VOICE)
        pitch = body.get("pitch", PITCH)
        volume = body.get("volume", VOLUME)

        texts = body.get("texts")
        if not isinstance(texts, list) or not texts:
            return _cors(400, {"error": "texts must be a non-empty array"})

        texts = [t.strip() for t in texts if t and t.strip()]
        if not texts:
            return _cors(400, {"error": "all texts are empty"})

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(
            asyncio.gather(*[_synthesize_one(t, voice, pitch, volume) for t in texts])
        )
        loop.close()

        audios = {}
        for text, audio_data in results:
            audios[text] = base64.b64encode(audio_data).decode("utf-8")

        return _cors(200, {"audios": audios, "format": "mp3"})

    except Exception as e:
        return _cors(500, {"error": str(e)})
