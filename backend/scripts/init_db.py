"""Script para inicializar la base de datos."""
from app.database import engine, Base
from app.models import Document, ChatMessage, Summary, Flashcard, Quiz, MonitoredFolder

print("Creando tablas en PostgreSQL...")
Base.metadata.create_all(bind=engine)
print("Tablas creadas exitosamente.")
