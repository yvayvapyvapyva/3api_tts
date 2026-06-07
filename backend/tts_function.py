#!/usr/bin/env python3
"""
tts_function.py — Yandex Cloud Function для синтеза речи через edge-tts

Использует Microsoft Edge TTS (бесплатно, без ключей).
Голос по умолчанию: ru-RU-DmitryNeural (как в commands_editor.py)

Зависимости (requirements-tts.txt):
  edge-tts>=6.0.0

Запрос: POST, JSON {"text": "текст", "voice": "ru-RU-DmitryNeural", "pitch": "-10Hz"}
Ответ:  JSON {"audio": "<base64 mp3>", "format": "mp3"}
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


def handler(event, context):
    try:
        if event.get("httpMethod") == "OPTIONS":
            return _cors(200, {"ok": True})

        if edge_tts is None:
            return _cors(500, {"error": "edge-tts not installed"})

        body = json.loads(event.get("body", "{}"))
        text = body.get("text", "").strip()
        if not text:
            return _cors(400, {"error": "empty text"})

        voice = body.get("voice", VOICE)
        pitch = body.get("pitch", PITCH)

        async def _synthesize():
            result = b""
            communicate = edge_tts.Communicate(text, voice=voice, pitch=pitch)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    result += chunk["data"]
            return result

        audio_data = asyncio.run(_synthesize())
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        return _cors(200, {"audio": audio_b64, "format": "mp3"})

    except Exception as e:
        return _cors(500, {"error": str(e)})
