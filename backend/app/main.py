from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import documents, chat, monitor, content, podcasts

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Study Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(monitor.router, prefix="/api/monitor", tags=["monitor"])
app.include_router(content.router, prefix="/api/content", tags=["content"])
app.include_router(podcasts.router, prefix="/api/podcasts", tags=["podcasts"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "study-assistant"}
