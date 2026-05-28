import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.document import Document
from app.schemas.schemas import DocumentResponse
from app.services.file_watcher import folder_monitor
from app.services.extractor import extract_text, calculate_hash
from app.services.chunker import chunk_document
from app.services.vector_store import vector_store
from app.services.n8n_trigger import trigger_n8n_workflow


class ChunkPayload(BaseModel):
    document_id: int
    filename: str
    chunk_number: int
    text: str


class N8nChunksRequest(BaseModel):
    chunks: list[ChunkPayload]

router = APIRouter()


@router.get("/")
def list_documents(page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    query = db.query(Document).order_by(Document.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@router.post("/process", response_model=DocumentResponse)
def process_document(filepath: str, db: Session = Depends(get_db)):
    import os
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="El archivo no existe")

    ext = os.path.splitext(filepath)[1].lower()
    supported = {".pdf", ".pptx", ".docx", ".txt", ".md"}
    if ext not in supported:
        raise HTTPException(status_code=400, detail=f"Formato no soportado: {ext}")

    file_hash = calculate_hash(filepath)
    existing = db.query(Document).filter(Document.file_hash == file_hash).first()
    if existing:
        return existing

    doc = Document(
        filename=os.path.basename(filepath),
        filepath=filepath,
        file_hash=file_hash,
        file_type=ext[1:],
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        text, pages = extract_text(filepath)
        doc.page_count = pages

        chunks = chunk_document(
            text, doc.id, doc.filename,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        vector_store.store_chunks(chunks, doc.id)

        trigger_n8n_workflow({
            "document_id": doc.id,
            "filename": doc.filename,
            "text": text,
        })

        doc.status = "processed"
    except Exception as e:
        doc.status = "error"
        print(f"[ERROR] processing {filepath}: {e}")

    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    vector_store.delete_document_chunks(doc_id)
    db.delete(doc)
    db.commit()
    return {"message": "Documento eliminado"}


@router.post("/n8n-chunks")
def receive_chunks_from_n8n(request: N8nChunksRequest):
    try:
        chunks_data = [c.model_dump() for c in request.chunks]
        doc_id = request.chunks[0].document_id if request.chunks else 0
        vector_store.store_chunks(chunks_data, doc_id)

        from app.database import SessionLocal
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = "processed"
                db.commit()
        finally:
            db.close()

        return {"status": "ok", "chunks_stored": len(request.chunks)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


class N8nWebhookPayload(BaseModel):
    body: dict


@router.post("/n8n-webhook")
def receive_webhook_from_n8n(payload: N8nWebhookPayload):
    try:
        data = payload.body
        doc_id = data.get("document_id")
        filename = data.get("filename", "unknown")
        text = data.get("text", "")

        if not text:
            return {"status": "error", "message": "No text in body"}

        from app.services.chunker import chunk_document
        chunks = chunk_document(text, doc_id, filename)
        vector_store.store_chunks(chunks, doc_id)

        from app.database import SessionLocal
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = "processed"
                db.commit()
        finally:
            db.close()

        return {"status": "ok", "chunks_stored": len(chunks), "document_id": doc_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/process-folder")
def process_folder(folder_path: str, db: Session = Depends(get_db)):
    import os
    from app.services.extractor import extract_text, calculate_hash
    from app.services.chunker import chunk_document
    from app.services.n8n_trigger import trigger_n8n_workflow
    from app.config import settings

    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="La carpeta no existe")

    supported = {".pdf", ".pptx", ".docx", ".md", ".txt"}
    processed = []
    skipped = []
    errors = []

    for root, _, files in os.walk(folder_path):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in supported:
                continue

            filepath = os.path.join(root, f)
            file_hash = calculate_hash(filepath)

            existing = db.query(Document).filter(
                Document.file_hash == file_hash
            ).first()
            if existing:
                skipped.append(f)
                continue

            doc = Document(
                filename=f,
                filepath=filepath,
                file_hash=file_hash,
                file_type=ext[1:],
                status="processing",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            import time as time_mod
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    text, pages = extract_text(filepath)
                    doc.page_count = pages
                    chunks = chunk_document(text, doc.id, f)
                    vector_store.store_chunks(chunks, doc.id)
                    trigger_n8n_workflow({
                        "document_id": doc.id,
                        "filename": f,
                        "text": text,
                    })
                    doc.status = "processed"
                    db.commit()
                    processed.append(f)
                    break
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                        import re
                        match = re.search(r'seconds:\s*(\d+)', err_str)
                        wait = int(match.group(1)) + 2 if match else 15
                        if attempt < max_retries - 1:
                            time_mod.sleep(wait)
                            continue
                    if attempt == max_retries - 1:
                        doc.status = "error"
                        db.commit()
                        errors.append({"file": f, "error": err_str[:200]})
                    break

    return {
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
        "total_processed": len(processed),
        "total_skipped": len(skipped),
        "total_errors": len(errors),
    }


@router.post("/sync")
def sync_from_monitored_folders(db: Session = Depends(get_db)):
    import os
    from app.models.document import MonitoredFolder
    from app.services.extractor import extract_text, calculate_hash
    from app.services.chunker import chunk_document
    from app.services.n8n_trigger import trigger_n8n_workflow
    from app.config import settings

    folders = db.query(MonitoredFolder).all()
    if not folders:
        raise HTTPException(status_code=400, detail="No hay carpetas monitoreadas")

    folder_paths = [f.folder_path for f in folders]
    supported = {".pdf", ".pptx", ".docx", ".md", ".txt"}

    added = []
    removed = []
    errors = []

    for folder_path in folder_paths:
        if not os.path.isdir(folder_path):
            continue
        for root, _, files in os.walk(folder_path):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext not in supported:
                    continue
                filepath = os.path.join(root, f)
                file_hash = calculate_hash(filepath)
                existing = db.query(Document).filter(
                    Document.file_hash == file_hash
                ).first()
                if existing and existing.status == "processed":
                    continue
                if existing:
                    vector_store.delete_document_chunks(existing.id)
                    db.delete(existing)
                    db.commit()

                doc = Document(
                    filename=f,
                    filepath=filepath,
                    file_hash=file_hash,
                    file_type=ext[1:],
                    status="processing",
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)

                try:
                    text, pages = extract_text(filepath)
                    doc.page_count = pages
                    chunks = chunk_document(
                        text, doc.id, f,
                        chunk_size=settings.chunk_size,
                        chunk_overlap=settings.chunk_overlap,
                    )
                    vector_store.store_chunks(chunks, doc.id)
                    trigger_n8n_workflow({
                        "document_id": doc.id,
                        "filename": f,
                        "text": text,
                    })
                    doc.status = "processed"
                    db.commit()
                    added.append(f)
                except Exception as e:
                    doc.status = "error"
                    db.commit()
                    errors.append({"file": f, "error": str(e)[:200]})

    all_docs = db.query(Document).all()
    for doc in all_docs:
        in_folder = any(
            doc.filepath.startswith(folder_path) for folder_path in folder_paths
        )
        if not in_folder:
            vector_store.delete_document_chunks(doc.id)
            db.delete(doc)
            removed.append(doc.filename)
    db.commit()

    return {
        "added": added,
        "removed": removed,
        "errors": errors,
        "total_added": len(added),
        "total_removed": len(removed),
        "total_errors": len(errors),
    }


@router.get("/{doc_id}/pdf")
def get_document_pdf(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pdf_path = doc.filepath.replace(".md", ".pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found for this document")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(pdf_path),
    )
