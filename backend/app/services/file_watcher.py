import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.database import SessionLocal
from app.models.document import Document
from app.services.extractor import extract_text, calculate_hash
from app.services.n8n_trigger import trigger_n8n_workflow


class DocumentHandler(FileSystemEventHandler):
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
        self.supported = {".pdf", ".pptx", ".docx", ".txt"}

    def on_created(self, event):
        if event.is_directory:
            return
        self._process_file(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._process_file(event.src_path)

    def _process_file(self, filepath: str):
        ext = Path(filepath).suffix.lower()
        if ext not in self.supported:
            return

        time.sleep(1)

        db = SessionLocal()
        try:
            file_hash = calculate_hash(filepath)
            filename = Path(filepath).name

            existing = db.query(Document).filter(
                Document.file_hash == file_hash
            ).first()

            if existing:
                return

            doc = Document(
                filename=filename,
                filepath=filepath,
                file_hash=file_hash,
                file_type=ext[1:],
                status="processing",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            text, pages = extract_text(filepath)
            doc.page_count = pages

            trigger_n8n_workflow({
                "document_id": doc.id,
                "filename": filename,
                "text": text,
            })

            doc.status = "processed"
            db.commit()

        except Exception as e:
            print(f"[ERROR] {filepath}: {e}")
            doc = db.query(Document).filter(Document.filepath == filepath).first()
            if doc:
                doc.status = "error"
                db.commit()
        finally:
            db.close()


class FolderMonitor:
    def __init__(self):
        self.observers: dict[str, Observer] = {}

    def add_folder(self, folder_path: str):
        if folder_path in self.observers:
            return

        Path(folder_path).mkdir(parents=True, exist_ok=True)
        event_handler = DocumentHandler(folder_path)
        observer = Observer()
        observer.schedule(event_handler, folder_path, recursive=False)
        observer.start()
        self.observers[folder_path] = observer

    def remove_folder(self, folder_path: str):
        observer = self.observers.pop(folder_path, None)
        if observer:
            observer.stop()
            observer.join()

    def stop_all(self):
        for observer in self.observers.values():
            observer.stop()
        for observer in self.observers.values():
            observer.join()
        self.observers.clear()


folder_monitor = FolderMonitor()
