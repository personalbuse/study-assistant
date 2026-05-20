import json
import os
import wave
import httpx
import base64
from app.services.groq_service import ask_groq
from app.config import settings

AUDIO_DIR = "/app/podcasts"

def generate_podcast_script(texts: list[str], title: str) -> list[dict]:
    combined = "\n\n---\n\n".join(texts)

    prompt = f"""Eres un guionista de podcasts educativos. Genera un guion de conversacion entre dos presentadores (HostA y HostB) discutiendo el siguiente contenido academico en ESPAÑOL.

Requisitos ESTRICTOS:
- Debe durar 10-12 minutos de conversacion natural (al menos 25 intercambios)
- Cada intervencion debe tener 2-4 parrafos de contenido sustancial
- HostA guia la conversacion, HostB hace preguntas y aporta ejemplos
- Incluye: introduccion, desarrollo de conceptos clave, ejemplos practicos, conclusion
- Usa un tono conversacional, no formal
- Alterna entre los dos presentadores

Devuelve SOLO JSON valido sin markdown:
{{
    "turns": [
        {{"speaker": "HostA", "text": "Bienvenidos a nuestro podcast educativo..."}},
        {{"speaker": "HostB", "text": "Hoy vamos a explorar..."}}
    ]
}}

Contenido:
{combined[:10000]}"""

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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"
    params = {"key": settings.google_api_key}

    body = {
        "contents": [{
            "parts": [{"text": script_text}]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": "zephyr"
                    }
                }
            }
        }
    }

    os.makedirs(AUDIO_DIR, exist_ok=True)
    wav_path = os.path.join(AUDIO_DIR, f"podcast_{podcast_id}.wav")

    try:
        with httpx.Client(timeout=300.0) as client:
            resp = client.post(url, params=params, json=body)
            resp.raise_for_status()
            data = resp.json()

        parts = data["candidates"][0]["content"]["parts"]
        audio_b64 = None
        for p in parts:
            if "inlineData" in p:
                audio_b64 = p["inlineData"]["data"]
                break

        if not audio_b64:
            raise Exception("No audio data in response")

        pcm_bytes = base64.b64decode(audio_b64)

        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_bytes)

        actual_duration = len(pcm_bytes) // (24000 * 2)

        try:
            from pydub import AudioSegment
            mp3_path = os.path.join(AUDIO_DIR, f"podcast_{podcast_id}.mp3")
            audio = AudioSegment.from_wav(wav_path)
            audio.export(mp3_path, format="mp3", bitrate="128k")
            os.remove(wav_path)
            return mp3_path, actual_duration
        except Exception:
            return wav_path, actual_duration

    except Exception as e:
        raise Exception(f"Error al sintetizar audio con Gemini TTS: {e}")
