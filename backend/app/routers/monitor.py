from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.document import MonitoredFolder, Document
from app.services.file_watcher import folder_monitor
from app.services.vector_store import vector_store
from app.schemas.schemas import FolderRequest, FolderResponse

router = APIRouter()


@router.get("/folders")
def list_folders(page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    query = db.query(MonitoredFolder).order_by(MonitoredFolder.created_at.desc())
    total = query.count()
    folders = query.offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {"id": f.id, "path": f.folder_path, "created_at": f.created_at.isoformat()}
        for f in folders
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/folders")
def add_folder(request: FolderRequest, db: Session = Depends(get_db)):
    existing = db.query(MonitoredFolder).filter(
        MonitoredFolder.folder_path == request.path
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="La carpeta ya está siendo monitoreada")

    folder = MonitoredFolder(folder_path=request.path)
    db.add(folder)
    db.commit()

    folder_monitor.add_folder(request.path)

    return {"message": "Carpeta agregada", "path": request.path}


@router.delete("/folders")
def remove_folder(request: FolderRequest, db: Session = Depends(get_db)):
    folder = db.query(MonitoredFolder).filter(
        MonitoredFolder.folder_path == request.path
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    docs = db.query(Document).filter(
        Document.filepath.startswith(request.path)
    ).all()
    for doc in docs:
        vector_store.delete_document_chunks(doc.id)
        db.delete(doc)

    db.delete(folder)
    db.commit()

    folder_monitor.remove_folder(request.path)

    return {"message": "Carpeta eliminada", "path": request.path}
