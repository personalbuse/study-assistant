from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.document import MonitoredFolder
from app.services.file_watcher import folder_monitor
from app.schemas.schemas import FolderRequest, FolderResponse

router = APIRouter()


@router.get("/folders")
def list_folders(db: Session = Depends(get_db)):
    folders = db.query(MonitoredFolder).all()
    return {
        "folders": [
            {"path": f.folder_path, "created_at": f.created_at.isoformat()}
            for f in folders
        ]
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

    db.delete(folder)
    db.commit()

    folder_monitor.remove_folder(request.path)

    return {"message": "Carpeta eliminada", "path": request.path}
