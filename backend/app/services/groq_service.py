import json
from groq import Groq
from app.config import settings

client = Groq(api_key=settings.groq_api_key)


def ask_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model=settings.groq_chat_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


def generate_summary(chunks_text: str) -> str:
    prompt = f"""Analiza el siguiente texto académico y genera un resumen estructurado.

Devuelve SOLO JSON válido sin markdown:

{{
    "summary": "resumen de 2-3 párrafos",
    "key_concepts": ["concepto1", "concepto2"],
    "main_topics": ["tema1", "tema2"],
    "study_questions": ["pregunta1?", "pregunta2?"]
}}

Texto:
{chunks_text}"""
    return ask_groq(prompt)


def generate_quiz(chunks_text: str, num_questions: int = 5) -> str:
    prompt = f"""Basado en el siguiente texto académico, genera {num_questions} preguntas de opción múltiple.

Devuelve SOLO JSON válido sin markdown:

{{
    "questions": [
        {{
            "question": "pregunta?",
            "options": ["a) opcion1", "b) opcion2", "c) opcion3", "d) opcion4"],
            "correct": "a)",
            "explanation": "por qué es correcta"
        }}
    ]
}}

Texto:
{chunks_text}"""
    return ask_groq(prompt)


def generate_flashcards(chunks_text: str) -> str:
    prompt = f"""Basado en el siguiente texto académico, genera 10 flashcards.

Devuelve SOLO JSON válido sin markdown:

{{
    "flashcards": [
        {{
            "question": "pregunta?",
            "answer": "respuesta",
            "topic": "tema"
        }}
    ]
}}

Texto:
{chunks_text}"""
    return ask_groq(prompt)
