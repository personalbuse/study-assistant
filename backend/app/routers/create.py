import os
import re
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.document import Document
from app.models.podcast import Podcast
from app.services.content_generator import generate_document_content
from app.services.pdf_generator import generate_pdf_from_markdown
from app.services.extractor import calculate_hash
from app.services.chunker import chunk_document
from app.services.vector_store import vector_store
from app.services.n8n_trigger import trigger_n8n_workflow
from app.services.podcast_service import generate_podcast_script, synthesize_audio
from app.config import settings

router = APIRouter()

CREATED_DIR = "/documents/created"


class CreateDocsRequest(BaseModel):
    topic: str


def _sanitize_topic(topic: str) -> str:
    safe = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ-]', '', topic).strip().lower()
    safe = re.sub(r'[-\s]+', '_', safe)
    return safe[:80]


def _save_and_process_document(topic: str, content: str, db: Session) -> Document:
    slug = _sanitize_topic(topic)
    folder = os.path.join(CREATED_DIR, slug)
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{slug}.md")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    pdf_path = os.path.join(folder, f"{slug}.pdf")
    try:
        generate_pdf_from_markdown(content, pdf_path)
    except Exception as e:
        print(f"[WARN] PDF generation failed for '{topic}': {e}")
        pdf_path = None

    file_hash = calculate_hash(filepath)
    existing = db.query(Document).filter(Document.file_hash == file_hash).first()
    if existing:
        return existing

    doc = Document(
        filename=f"{slug}.md",
        filepath=filepath,
        file_hash=file_hash,
        file_type="md",
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        chunks = chunk_document(
            content, doc.id, doc.filename,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        vector_store.store_chunks(chunks, doc.id)

        trigger_n8n_workflow({
            "document_id": doc.id,
            "filename": doc.filename,
            "text": content,
        })

        doc.status = "processed"
    except Exception as e:
        doc.status = "error"
        print(f"[ERROR] processing created doc {doc.id}: {e}")

    db.commit()
    db.refresh(doc)
    return doc


@router.post("/docs")
def create_docs(request: CreateDocsRequest, db: Session = Depends(get_db)):
    topic = request.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    content = generate_document_content(topic)
    if not content.strip():
        raise HTTPException(status_code=500, detail="Generated content is empty")

    doc = _save_and_process_document(topic, content, db)

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "filepath": doc.filepath,
        "status": doc.status,
        "topic": topic,
    }


@router.post("/podcast")
def create_podcast(request: CreateDocsRequest, db: Session = Depends(get_db)):
    topic = request.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    content = generate_document_content(topic)
    if not content.strip():
        raise HTTPException(status_code=500, detail="Generated content is empty")

    doc = _save_and_process_document(topic, content, db)

    texts = vector_store.get_document_texts(doc.id)
    if not texts:
        texts = [content]

    turns, duration = generate_podcast_script(texts, doc.filename)

    podcast = Podcast(
        title=f"Podcast - {doc.filename.replace('.md', '')}",
        document_id=doc.id,
        source_count=1,
        script=json.dumps(turns, ensure_ascii=False),
        duration_seconds=duration,
    )
    db.add(podcast)
    db.commit()
    db.refresh(podcast)

    try:
        audio_path, actual_duration = synthesize_audio(turns, podcast.id)
        podcast.audio_path = audio_path
        podcast.duration_seconds = actual_duration
        db.commit()
    except Exception as e:
        db.delete(podcast)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "id": podcast.id,
        "title": podcast.title,
        "document_id": doc.id,
        "source_count": podcast.source_count,
        "duration_seconds": podcast.duration_seconds,
        "created_at": podcast.created_at.isoformat(),
    }
