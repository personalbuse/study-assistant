import json
import os
import httpx
import base64
from app.services.groq_service import ask_groq
from app.config import settings

AUDIO_DIR = "/app/podcasts"
DURATION_WORDS = 1800

def generate_podcast_script(texts: list[str], title: str) -> list[dict]:
    combined = "\n\n---\n\n".join(texts)
    target_words = DURATION_WORDS

    prompt = f"""Eres un guionista de podcasts educativos. Genera un guion de conversacion entre dos presentadores (HostA y HostB) discutiendo el siguiente contenido academico en ESPAÑOL.

Requisitos:
- Debe durar aproximadamente 10-12 minutos de conversacion natural
- HostA guia la conversacion, HostB hace preguntas y aporta ejemplos
- Incluye: introduccion, desarrollo de conceptos clave, ejemplos practicos, conclusion
- Usa un tono conversacional, no formal
- Alterna entre los dos presentadores cada 2-4 intercambios aproximadamente

Devuelve SOLO JSON valido sin markdown:
{{
    "turns": [
        {{"speaker": "HostA", "text": "Bienvenidos a nuestro podcast educativo..."}},
        {{"speaker": "HostB", "text": "Hoy vamos a explorar..."}}
    ]
}}

Contenido:
{combined[:8000]}"""

    raw = ask_groq(prompt)
    try:
        data = json.loads(raw.strip("```json\n").strip("```").strip())
        turns = data.get("turns", [])
    except json.JSONDecodeError:
        turns = [{"speaker": "HostA", "text": raw}]

    word_count = sum(len(t["text"].split()) for t in turns)
    duration_est = max(word_count // 150, 1)
    return turns, duration_est


def synthesize_audio(turns: list[dict], podcast_id: int) -> str:
    script_text = "\n".join(f"{t['speaker']}: {t['text']}" for t in turns)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-tts:generateContent"
    params = {"key": settings.google_api_key}

    body = {
        "contents": [{
            "parts": [{"text": f"Lee el siguiente guion de podcast en español usando dos voces diferentes, una para cada presentador:\n\n{script_text}"}]
        }],
        "generationConfig": {
            "responseModality": "audio",
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": "es-ES-Standard-A"
                    }
                }
            }
        }
    }

    os.makedirs(AUDIO_DIR, exist_ok=True)
    output_path = os.path.join(AUDIO_DIR, f"podcast_{podcast_id}.mp3")

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, params=params, json=body)
            resp.raise_for_status()
            data = resp.json()

        parts = data["candidates"][0]["content"]["parts"]
        audio_b64 = None
        for p in parts:
            if "inlineData" in p and p["inlineData"].get("mimeType", "").startswith("audio/"):
                audio_b64 = p["inlineData"]["data"]
                break

        if not audio_b64:
            raise Exception("No audio data in response")

        audio_bytes = base64.b64decode(audio_b64)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)

    except Exception as e:
        raise Exception(f"Error al sintetizar audio con Gemini TTS: {e}")

    return output_path
