from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.vector_store import vector_store
from app.services.groq_service import ask_groq
from app.models.chat import ChatMessage

router = APIRouter()


@router.post("/ask")
def ask_question(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        relevant_chunks = vector_store.search(request.message, top_k=20)

        context = "\n\n".join([
            f"[{chunk['filename']} - Página {chunk['page']}]\n{chunk['text']}"
            for chunk in relevant_chunks
        ])

        prompt = f"""Eres un asistente de estudio académico experto.

Tienes acceso al siguiente contexto extraído de documentos del estudiante:
--------------------
{context}
--------------------

Responde la pregunta del estudiante de la forma más completa y detallada posible.
Usa el contexto como fuente principal de información, pero si la pregunta va más
allá de lo que hay en el texto, complementa con tu conocimiento general.

Pregunta: {request.message}

Respuesta detallada (en español):"""

        answer = ask_groq(prompt)

    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
            answer = "Límite de consultas a Groq excedido. Espera un momento y vuelve a intentarlo."
        elif "content_filter" in error_msg.lower():
            answer = "La respuesta fue bloqueada por filtros de seguridad. Reformula tu pregunta."
        else:
            answer = f"Error al procesar: {error_msg[:100]}"

        return ChatResponse(
            answer=answer,
            sources=[],
        )

    chat_msg = ChatMessage(
        question=request.message,
        answer=answer,
        sources=[c["filename"] for c in relevant_chunks],
    )
    db.add(chat_msg)
    db.commit()

    return ChatResponse(
        answer=answer,
        sources=[
            {
                "filename": c["filename"],
                "page": c["page"],
                "relevance": round(c["score"], 3),
            }
            for c in relevant_chunks
        ],
    )


@router.get("/history")
def get_chat_history(db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).order_by(ChatMessage.created_at.asc()).all()
    return [
        {
            "id": m.id,
            "question": m.question,
            "answer": m.answer,
            "sources": m.sources,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
