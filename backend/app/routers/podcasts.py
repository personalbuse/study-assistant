import os
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.document import Document, MonitoredFolder
from app.models.podcast import Podcast
from app.services.vector_store import vector_store
from app.services.podcast_service import generate_podcast_script, synthesize_audio

router = APIRouter()


@router.post("/by-document/{document_id}")
def create_podcast_by_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    texts = vector_store.get_document_texts(document_id)
    if not texts:
        raise HTTPException(status_code=400, detail="No hay contenido para este documento")

    turns, duration = generate_podcast_script(texts, doc.filename)

    podcast = Podcast(
        title=f"Podcast - {doc.filename}",
        document_id=document_id,
        source_count=1,
        script=json.dumps(turns, ensure_ascii=False),
        duration_seconds=duration,
    )
    db.add(podcast)
    db.commit()
    db.refresh(podcast)

    try:
        audio_path = synthesize_audio(turns, podcast.id)
        podcast.audio_path = audio_path
        db.commit()
    except Exception as e:
        db.delete(podcast)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "id": podcast.id,
        "title": podcast.title,
        "source_count": podcast.source_count,
        "duration_seconds": podcast.duration_seconds,
        "created_at": podcast.created_at.isoformat(),
    }


@router.post("/by-folder/{folder_id}")
def create_podcast_by_folder(folder_id: int, db: Session = Depends(get_db)):
    folder = db.query(MonitoredFolder).filter(MonitoredFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    docs = db.query(Document).filter(
        Document.filepath.startswith(folder.folder_path),
        Document.status == "processed",
    ).all()
    if not docs:
        raise HTTPException(status_code=400, detail="No hay documentos procesados en esta carpeta")

    doc_ids = [d.id for d in docs]
    all_texts = []
    for did in doc_ids:
        all_texts.extend(vector_store.get_document_texts(did))

    if not all_texts:
        raise HTTPException(status_code=400, detail="No hay contenido en los documentos")

    folder_name = os.path.basename(folder.folder_path.rstrip("/"))
    turns, duration = generate_podcast_script(all_texts, folder_name)

    podcast = Podcast(
        title=f"Podcast - {folder_name}",
        folder_path=folder.folder_path,
        source_count=len(docs),
        script=json.dumps(turns, ensure_ascii=False),
        duration_seconds=duration,
    )
    db.add(podcast)
    db.commit()
    db.refresh(podcast)

    try:
        audio_path = synthesize_audio(turns, podcast.id)
        podcast.audio_path = audio_path
        db.commit()
    except Exception as e:
        db.delete(podcast)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "id": podcast.id,
        "title": podcast.title,
        "source_count": podcast.source_count,
        "duration_seconds": podcast.duration_seconds,
        "created_at": podcast.created_at.isoformat(),
    }


@router.get("/")
def list_podcasts(db: Session = Depends(get_db)):
    podcasts = db.query(Podcast).order_by(Podcast.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "source_count": p.source_count,
            "duration_seconds": p.duration_seconds,
            "has_audio": bool(p.audio_path and os.path.exists(p.audio_path)),
            "created_at": p.created_at.isoformat(),
        }
        for p in podcasts
    ]


@router.get("/{podcast_id}/audio")
def get_podcast_audio(podcast_id: int, db: Session = Depends(get_db)):
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast no encontrado")
    if not podcast.audio_path or not os.path.exists(podcast.audio_path):
        raise HTTPException(status_code=404, detail="Audio no encontrado")
    return FileResponse(podcast.audio_path, media_type="audio/mpeg")


@router.delete("/{podcast_id}")
def delete_podcast(podcast_id: int, db: Session = Depends(get_db)):
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast no encontrado")

    if podcast.audio_path and os.path.exists(podcast.audio_path):
        os.remove(podcast.audio_path)

    db.delete(podcast)
    db.commit()
    return {"message": "Podcast eliminado"}
