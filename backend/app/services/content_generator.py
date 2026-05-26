from app.services.groq_service import ask_groq


def generate_document_content(topic: str) -> str:
    prompt = f"""Eres un profesor universitario. Genera un documento educativo detallado en ESPAÑOL sobre: {topic}.

Estructura requerida (en markdown):
1. Título y descripción general del tema
2. Introducción
3. Conceptos fundamentales con explicaciones claras
4. Desarrollo detallado: subtemas, clasificaciones, normas aplicables
5. Ejemplos prácticos y aplicaciones del mundo real
6. Conclusión
7. Referencias y documentos/normas relacionadas

Requisitos:
- Extensión mínima: 1500 palabras
- Usa un tono académico pero accesible
- Incluye definiciones técnicas cuando sea relevante
- Los ejemplos deben ser concretos y aplicables
- Organiza con títulos (##) y subtítulos (###)
- Usa listas con viñetas para conceptos clave

Devuelve SOLO el contenido del documento en markdown, sin JSON ni metadatos extras."""
    return ask_groq(prompt)
