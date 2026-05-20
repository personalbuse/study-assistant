import os
import sys
import time
import json
import hashlib
import requests
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

API_URL = "http://localhost:8000"
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/file-watcher"
SUPPORTED = {".pdf", ".pptx", ".docx", ".md", ".txt"}
POLL_INTERVAL = 5
HASH_FILE = os.path.join(os.path.dirname(__file__), "..", "processed_hashes.json")


class WatcherHandler(FileSystemEventHandler):
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.processed = load_hashes()

    def on_created(self, event):
        if event.is_directory:
            return
        self._process(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._process(event.src_path)

    def _process(self, filepath):
        ext = Path(filepath).suffix.lower()
        if ext not in SUPPORTED:
            return

        time.sleep(1)
        file_hash = calculate_hash(filepath)
        if file_hash in self.processed:
            return

        filename = Path(filepath).name
        print(f"[WATCHER] Nuevo archivo: {filename}")

        try:
            resp = requests.post(
                f"{N8N_WEBHOOK_URL}",
                json={"filepath": filepath},
                timeout=120,
            )
            if resp.status_code == 200:
                self.processed.add(file_hash)
                save_hashes(self.processed)
                print(f"  ✅ {filename} enviado a n8n")
            else:
                print(f"  ❌ {filename} error: {resp.text}")
        except Exception as e:
            print(f"  ❌ {filename} error conexión: {e}")


def calculate_hash(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_hashes() -> set:
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE) as f:
            return set(json.load(f))
    return set()


def save_hashes(hashes: set):
    with open(HASH_FILE, "w") as f:
        json.dump(list(hashes), f)


def scan_existing_files(folder_path: str):
    handler = WatcherHandler(folder_path)
    count = 0
    for root, _, files in os.walk(folder_path):
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in SUPPORTED:
                filepath = os.path.join(root, f)
                file_hash = calculate_hash(filepath)
                if file_hash not in handler.processed:
                    handler._process(filepath)
                    count += 1
    if count == 0:
        print(f"[WATCHER] No hay archivos nuevos en {folder_path}")


def monitor_folder(folder_path: str):
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    event_handler = WatcherHandler(folder_path)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=True)
    observer.start()
    print(f"[WATCHER] Monitoreando: {folder_path}")
    return observer


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Host File Watcher")
    parser.add_argument("folder", nargs="?", help="Carpeta a monitorear")
    parser.add_argument("--scan", action="store_true", help="Escanear archivos existentes")
    parser.add_argument("--daemon", action="store_true", help="Correr en segundo plano")
    args = parser.parse_args()

    if not args.folder:
        folders = []
        try:
            resp = requests.get(f"{API_URL}/api/monitor/folders", timeout=5)
            if resp.status_code == 200:
                folders = [f["path"] for f in resp.json().get("folders", [])]
        except:
            pass

        if not folders:
            print("[WATCHER] No hay carpetas configuradas. Especifica una carpeta:")
            print("  python watcher_host.py /ruta/a/mi/carpeta")
            sys.exit(1)

        for folder in folders:
            observers = []
            if args.scan:
                scan_existing_files(folder)
            obs = monitor_folder(folder)
            observers.append(obs)

            if not args.daemon:
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    for o in observers:
                        o.stop()
                    for o in observers:
                        o.join()
                    print("[WATCHER] Detenido")
    else:
        if args.scan:
            scan_existing_files(args.folder)
        obs = monitor_folder(args.folder)
        if not args.daemon:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                obs.stop()
                obs.join()
                print("[WATCHER] Detenido")


if __name__ == "__main__":
    main()
