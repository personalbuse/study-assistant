import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document
from app.models.quiz import Summary, Flashcard, Quiz
from app.services.groq_service import generate_summary, generate_quiz, generate_flashcards
from app.services.vector_store import vector_store

router = APIRouter()


@router.post("/summaries/{document_id}")
def create_summary(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    existing = db.query(Summary).filter(Summary.document_id == document_id).first()
    if existing:
        return existing

    results = vector_store.search(f"Resumen completo de {doc.filename}", top_k=20)
    combined_text = "\n\n".join([r["text"] for r in results])

    raw = generate_summary(combined_text)
    try:
        data = json.loads(raw.strip("```json\n").strip("```").strip())
    except json.JSONDecodeError:
        data = {"summary": raw, "key_concepts": [], "main_topics": [], "study_questions": []}

    summary = Summary(
        document_id=document_id,
        summary=data.get("summary", raw),
        key_concepts=data.get("key_concepts", []),
        main_topics=data.get("main_topics", []),
        study_questions=data.get("study_questions", []),
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


@router.get("/summaries/{document_id}")
def get_summary(document_id: int, db: Session = Depends(get_db)):
    summary = db.query(Summary).filter(Summary.document_id == document_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Resumen no encontrado")
    return summary


@router.post("/flashcards/{document_id}")
def create_flashcards(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    existing = db.query(Flashcard).filter(Flashcard.document_id == document_id).all()
    if existing:
        return existing

    results = vector_store.search(f"Conceptos importantes de {doc.filename}", top_k=20)
    combined_text = "\n\n".join([r["text"] for r in results])

    raw = generate_flashcards(combined_text)
    try:
        data = json.loads(raw.strip("```json\n").strip("```").strip())
        cards = data.get("flashcards", [])
    except json.JSONDecodeError:
        cards = []

    created = []
    for card in cards:
        fc = Flashcard(
            document_id=document_id,
            question=card.get("question", ""),
            answer=card.get("answer", ""),
            topic=card.get("topic", ""),
        )
        db.add(fc)
        created.append(fc)
    db.commit()
    for c in created:
        db.refresh(c)
    return created


@router.get("/flashcards/{document_id}")
def list_flashcards(document_id: int, db: Session = Depends(get_db)):
    cards = db.query(Flashcard).filter(Flashcard.document_id == document_id).all()
    return cards


@router.post("/quizzes/{document_id}")
def create_quiz(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    existing = db.query(Quiz).filter(Quiz.document_id == document_id).first()
    if existing:
        return existing

    results = vector_store.search(f"Contenido del documento {doc.filename}", top_k=20)
    combined_text = "\n\n".join([r["text"] for r in results])

    raw = generate_quiz(combined_text)
    try:
        data = json.loads(raw.strip("```json\n").strip("```").strip())
        questions = data.get("questions", [])
    except json.JSONDecodeError:
        questions = []

    quiz = Quiz(
        document_id=document_id,
        title=f"Quiz - {doc.filename}",
        questions=questions,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


@router.get("/quizzes/{document_id}")
def get_quiz(document_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.document_id == document_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz no encontrado")
    return quiz
