# Study Assistant — Asistente de Estudio Académico

Asistente de estudio personal con procesamiento automatizado de documentos, chat con RAG (Retrieval-Augmented Generation), y generación de podcasts educativos. Todo corre localmente con Docker.

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────┐
│                    Host (tu PC)                         │
│                                                         │
│  ┌──────────┐   ┌──────────┐   ┌────────────────────┐  │
│  │ Electron │   │ Frontend │   │ watcher_host.py    │  │
│  │ (ventana)│◄─►│ (Vite +  │   │ (watchdog nativo)  │  │
│  │          │   │  React)  │   │                    │  │
│  └──────────┘   └────┬─────┘   └─────────┬──────────┘  │
│                      │                   │             │
│                  :5173               llama a webhook   │
│                      │                   │             │
└──────────────────────┼───────────────────┼─────────────┘
                       │                   │
                  HTTP │               HTTP│
                       ▼                   ▼
              ┌──────────────────────────────────┐
              │        Docker Network             │
              │        study-net                  │
              │                                   │
              │  ┌─────────┐   ┌──────────────┐  │
              │  │ Backend │──►│ PostgreSQL   │  │
              │  │ FastAPI  │   │ (metadatos)  │  │
              │  │ :8000   │   └──────────────┘  │
              │  │         │   ┌──────────────┐  │
              │  │         │──►│ Qdrant       │  │
              │  │         │   │ (vectores)   │  │
              │  └────┬────┘   └──────────────┘  │
              │       │                          │
              │  ┌────▼────┐                     │
              │  │ n8n     │                     │
              │  │ :5678   │                     │
              │  └─────────┘                     │
              └──────────────────────────────────┘
                       │
                       │ APIs externas
                       ▼
              ┌──────────────────┐
              │  Groq (LLM)      │
              │  llama-3.3-70b   │
              └──────────────────┘
              ┌──────────────────┐
              │  Gemini TTS      │
              │  (podcast audio) │
              └──────────────────┘
```

---

## ¿Por qué n8n?

| Problema                        | Solución con n8n                            |
|--------------------------------|----------------------------------------------|
| Procesamiento de documentos es lento y bloquea el backend | Se delega a n8n como workflow asíncrono |
| Se necesita reintentar con backoff ante errores | n8n maneja retry logic nativamente |
| Extracción de texto + chunking + embedding en tándem | Flujo visual encadenado |
| El frontend no debe esperar a que termine | Webhook HTTP → n8n procesa → callback al backend |

n8n actúa como **orquestador de procesamiento**. Cuando un documento llega:
1. Backend extrae texto (rápido) y guarda metadata en PostgreSQL
2. Backend envía texto a n8n via webhook interno (`POST /webhook/process-document`)
3. n8n ejecuta un workflow que:
   - Recibe el texto
   - Puede aplicar transformaciones adicionales
   - Llama al endpoint `/api/documents/n8n-chunks` del backend para guardar los chunks vectorizados en Qdrant
4. Backend marca el documento como `processed`

El workflow `file_watcher.json` se activa desde un script Python (`watcher_host.py`) que corre en el **host** (no dentro de Docker) usando `watchdog` para detectar archivos nuevos en carpetas monitoreadas.

### Workflows incluidos

| Archivo | Propósito |
|---------|-----------|
| `workflows/file_watcher.json` | Webhook de entrada desde watcher_host.py → envía a backend |
| `workflows/process_document.json` | Procesamiento de documentos (v1, más simple) |
| `workflows/process_document_v2.json` | Procesamiento mejorado con manejo de errores |

---

## ¿Por qué Qdrant?

| Alternativa     | Problema                                      |
|----------------|------------------------------------------------|
| pgvector       | Requiere extensión PostgreSQL, no aislado     |
| Pinecone       | Servicio en la nube, requiere API key, costos |
| ChromaDB       | Menos maduro, sin persistencia robusta        |
| Weaviate       | Más pesado, overkill para single-user         |

Qdrant es:
- **Ligero** — imagen Docker de ~60MB, corre con 256MB RAM
- **Rápido** — búsqueda coseno en 384 dimensiones en milisegundos
- **Persistente** — monta volumen para no perder datos
- **API REST** — se comunica con el backend via HTTP en el puerto 6333
- **Filtros** — soporta filtrado por `document_id` para eliminar chunks de un documento específico

**Embeddings**: Se usa `fastembed` (biblioteca local, sin GPU) con el modelo `paraphrase-multilingual-MiniLM-L12-v2` que produce vectores de 384 dimensiones. Corre completamente offline.

---

## Stack Tecnológico

### Backend (`backend/`)

| Componente       | Tecnología                         |
|-----------------|------------------------------------|
| Framework API   | FastAPI (Python 3.12)              |
| ORM             | SQLAlchemy 2.0                     |
| Base de datos   | PostgreSQL 16 (Alpine)             |
| Vector store    | Qdrant v1.18                       |
| Embeddings      | fastembed 0.3.3 (local, offline)   |
| LLM             | Groq API (`llama-3.3-70b-versatile`) |
| TTS             | Google Gemini (`gemini-2.5-flash-preview-tts`) |
| OCR             | Tesseract + pdf2image (para PPTX con imágenes) |
| Procesamiento   | pypdf, pdfplumber, python-pptx, python-docx |
| Audio           | pydub + ffmpeg (PCM→WAV→MP3) |

### Frontend (`frontend/`)

| Componente   | Tecnología                    |
|-------------|-------------------------------|
| Framework   | React 18 + Vite              |
| Estilos     | Tailwind CSS + CSS variables |
| HTTP client | Axios                        |
| Empaquetado | Vite 5                       |

### Desktop (`electron/`)

| Componente   | Tecnología         |
|-------------|-------------------|
| Ventana     | Electron          |
| IPC         | contextBridge + ipcRenderer |
| Folder picker | `dialog.showOpenDialog` |

### Infraestructura

| Componente | Tecnología                          |
|-----------|-------------------------------------|
| Contenedores | Docker Compose                    |
| Red interna  | `study-net` (bridge)              |
| Orquestación | n8n (workflows visuales)          |

---

## Estructura del Backend

```
backend/
├── Dockerfile
├── requirements.txt
├── watcher_host.py          # Script host-side para watch de carpetas
└── app/
    ├── main.py               # FastAPI app, CORS, rutas
    ├── config.py             # Settings (GROQ_API_KEY, GOOGLE_API_KEY, etc.)
    ├── database.py           # SQLAlchemy engine + session
    ├── schemas/
    │   └── schemas.py        # Pydantic models (request/response)
    ├── models/
    │   ├── document.py       # Document, MonitoredFolder
    │   ├── chat.py           # ChatMessage
    │   ├── quiz.py           # Summary, Flashcard, Quiz
    │   └── podcast.py        # Podcast
    ├── routers/
    │   ├── documents.py      # CRUD documentos, sync, process, webhooks n8n
    │   ├── chat.py           # /api/chat/ask (RAG), /api/chat/history
    │   ├── monitor.py        # /api/monitor/folders (CRUD)
    │   ├── content.py        # /api/content/summaries, /flashcards, /quizzes
    │   └── podcasts.py       # /api/podcasts (by-document, by-folder, audio)
    └── services/
        ├── embeddings.py     # fastembed wrapper (singleton)
        ├── vector_store.py   # Qdrant client (store, search, delete, scroll)
        ├── extractor.py      # PDF/PPTX/DOCX/TXT/MD → texto (con OCR)
        ├── chunker.py        # Texto → chunks de ~500 palabras con overlap
        ├── groq_service.py   # Groq API wrapper (chat, summaries, quiz, flashcards)
        ├── podcast_service.py# Groq script gen + Gemini TTS synthesis
        ├── n8n_trigger.py    # HTTP call to n8n webhook
        └── file_watcher.py   # watchdog observer (in-container)
```

### API Endpoints

**Documentos** (`/api/documents`)
- `GET /` — Listar documentos
- `GET /{id}` — Obtener documento por ID
- `POST /process?filepath=` — Procesar archivo (extraer + chunk + store + n8n)
- `POST /process-folder?folder_path=` — Procesar todos los archivos de una carpeta
- `POST /sync` — Sincronizar desde carpetas monitoreadas (agrega nuevos, elimina huérfanos)
- `POST /n8n-chunks` — Webhook para que n8n guarde chunks procesados
- `POST /n8n-webhook` — Webhook alternativo para n8n
- `DELETE /{id}` — Eliminar documento + sus chunks vectoriales

**Chat** (`/api/chat`)
- `POST /ask` — Pregunta con RAG (search Qdrant → contexto → Groq)
- `GET /history` — Historial de mensajes

**Monitor** (`/api/monitor`)
- `GET /folders` — Listar carpetas monitoreadas
- `POST /folders` — Agregar carpeta
- `DELETE /folders` — Eliminar carpeta (cascade-delete documentos + chunks)

**Contenido** (`/api/content`)
- `POST /summaries/{id}` / `GET /summaries/{id}` — Resumen
- `POST /flashcards/{id}` / `GET /flashcards/{id}` — Flashcards
- `POST /quizzes/{id}` / `GET /quizzes/{id}` — Quiz (con preguntas de opción múltiple)

**Podcasts** (`/api/podcasts`)
- `POST /by-document/{id}` — Generar podcast de un documento
- `POST /by-folder/{id}` — Generar podcast de toda una carpeta
- `GET /` — Listar podcasts
- `GET /{id}/audio` — Descargar audio (MP3 o WAV)
- `DELETE /{id}` — Eliminar podcast + archivo de audio

---

## Estructura del Frontend

```
frontend/
├── package.json
├── vite.config.js           # Proxy /api → localhost:8000
└── src/
    ├── main.jsx             # Entry point React
    ├── App.jsx              # Router de vistas, theme toggle, state global
    ├── index.css            # Tema CSS variables (light/dark)
    ├── api/
    │   └── client.js        # Axios instance
    └── components/
        ├── Sidebar.jsx      # Navegación lateral (7 vistas + theme toggle)
        ├── Dashboard.jsx    # Vista principal con cards resumen
        ├── DocumentList.jsx # Lista de documentos procesados
        ├── FolderPicker.jsx # Gestión de carpetas monitoreadas
        ├── ChatWindow.jsx   # Chat con RAG (pregunta → contexto → respuesta)
        ├── Flashcards.jsx   # Flashcards por documento
        ├── QuizViewer.jsx   # Quiz interactivo por documento
        └── PodcastViewer.jsx# Podcasts con 2 tabs (documento/carpeta) y audio player
```

### Vistas (7)

| Vista       | Componente       | Descripción                                    |
|-------------|------------------|------------------------------------------------|
| Dashboard   | Dashboard        | Resumen: docs, carpetas, links rápidos         |
| Documentos  | DocumentList     | Tabla con nombre, tipo, estado, fecha          |
| Carpetas    | FolderPicker     | Agregar/quitar carpetas monitoreadas + sync    |
| Chat        | ChatWindow       | Conversación RAG con contexto de documentos   |
| Flashcards  | Flashcards       | Tarjetas de estudio por documento              |
| Quizzes     | QuizViewer       | Preguntas de opción múltiple por documento     |
| Podcasts    | PodcastViewer    | Generar y escuchar podcasts                    |

### Tema

CSS variables puras sin dependencias de theming. Light mode: fondo blanco (#ffffff), texto negro (#000000). Dark mode: fondo negro (#000000), texto blanco (#ffffff). Escala de grises neutros — cero tonos azules o slate.

---

## Pipeline de Datos

### Procesamiento de Documentos

```
Archivo (PDF/PPTX/DOCX/MD/TXT)
    │
    ▼
watcher_host.py (detecta en host)
    │
    ├──► n8n webhook (workflow file_watcher)
    │       │
    │       └──► Backend /api/documents/process
    │               │
    ▼               ▼
        extract_text()
            │
            ├── PDF: pdfplumber → texto por página
            ├── PPTX: python-pptx → texto slides + OCR imágenes
            ├── DOCX: python-docx → párrafos + tablas
            └── TXT/MD: lectura directa
            │
            ▼
        chunk_document()
            │
            ├── Divide en fragmentos de ~500 palabras
            ├── Overlap de 50 palabras entre chunks
            └── Detecta saltos de página/diapositiva
            │
            ▼
        vector_store.store_chunks()
            │
            ├── fastembed → vector 384-dim por chunk
            └── Qdrant upsert (payload: document_id, filename, page, text)
            │
            ▼
        trigger_n8n_workflow()
            │
            └── n8n procesa asíncronamente, callback a /n8n-chunks
```

### Chat con RAG

```
Pregunta del usuario
    │
    ▼
vector_store.search(query, top_k=20)
    │
    ├── fastembed → vector de la pregunta
    └── Qdrant búsqueda coseno → top 20 chunks relevantes
    │
    ▼
ask_groq(prompt con contexto + pregunta)
    │
    ├── Groq llama-3.3-70b-versatile
    └── Respuesta detallada en español
    │
    ▼
Guarda en ChatMessage (PostgreSQL)
    │
    ▼
Devuelve respuesta + fuentes (filename, page, score)
```

### Podcast

```
Seleccionar documento o carpeta
    │
    ▼
vector_store.get_document_texts(document_id)
    │
    ├── Qdrant scroll filter por document_id
    └── Recupera todos los chunks de texto
    │
    ▼
generate_podcast_script(texts)
    │
    ├── Groq genera guion conversacional (HostA + HostB)
    └── JSON con turns: [{speaker, text}, ...]
    │
    ▼
synthesize_audio(turns, podcast_id)
    │
    ├── Gemini TTS (gemini-2.5-flash-preview-tts)
    │   POST generateContent con responseModalities: ["AUDIO"]
    │   Voz: star name (ej: "zephyr")
    ├── Decodifica PCM 24kHz 16-bit mono
    ├── Guarda como WAV
    ├── Convierte a MP3 con pydub + ffmpeg
    └── Duración real calculada: bytes / (24000 × 2)
```

---

## Configuración y Despliegue

### Prerequisitos

- Docker + Docker Compose
- Node.js 18+ (para frontend y Electron)
- Python 3.10+ (para watcher_host.py)
- API keys:
  - Groq: https://console.groq.com (modelo usado: `llama-3.3-70b-versatile`)
  - Google: https://aistudio.google.com (para Gemini TTS, modelo: `gemini-2.5-flash-preview-tts`)

### Variables de Entorno (`.env`)

```env
GROQ_API_KEY=gsk_tu_key_aqui
GOOGLE_API_KEY=AIza_tu_key_aqui
```

Ambas se pasan al contenedor backend via `docker-compose.yml`.

### Levantar el Proyecto

```bash
# 1. Clonar y configurar
cp .env.example .env   # Editar con tus API keys
mkdir -p documents podcasts

# 2. Iniciar servicios Docker
docker compose up -d

# 3. Verificar estado
curl http://localhost:8000/api/health
# → {"status":"ok","service":"study-assistant"}

# 4. Iniciar frontend (desarrollo)
cd frontend && npm install && npm run dev
# → http://localhost:5173

# 5. (Opcional) Iniciar watcher host-side
python backend/watcher_host.py --daemon

# 6. (Opcional) Iniciar en Electron
cd electron && npm install && npm run dev
```

### Servicios

| Servicio    | Puerto | URL                     |
|-------------|--------|-------------------------|
| Backend     | 8000   | http://localhost:8000   |
| Frontend    | 5173   | http://localhost:5173   |
| n8n         | 5678   | http://localhost:5678   |
| Qdrant      | 6333   | http://localhost:6333   |
| PostgreSQL  | 5433   | postgresql://localhost:5433 |

### Activar n8n Workflows

1. Ir a http://localhost:5678
2. Configurar cuenta (primera vez)
3. Ir a Workflows → Import from File
4. Importar `workflows/file_watcher.json`
5. Toggle "Active" para activar el webhook
6. (Si no hay callback a backend, ajustar URL en el nodo HTTP Request)

---

## Decisiones Técnicas Clave

| Decisión | Razón |
|----------|-------|
| **Groq como LLM principal** (no Gemini) | Gemini tuvo problemas de cuota (429); Groq es rápido, estable, y el modelo `llama-3.3-70b` da buena calidad académica |
| **Gemini solo para TTS** | `gemini-2.5-flash-preview-tts` produce audio de alta calidad; la API usa `responseModalities: ["AUDIO"]` (array plural) y nombres de voz tipo estrellas (e.g. "zephyr") |
| **fastembed local** | Embeddings offline, sin llamadas HTTP ni costos recurrentes; modelo multilingüe (español) |
| **384 dimensiones** | Modelo `paraphrase-multilingual-MiniLM-L12-v2` = 384d. Balance entre velocidad y calidad |
| **PostgreSQL + Qdrant** | Split: metadata y datos relacionales en Postgres, vectores de búsqueda semántica en Qdrant |
| **Múltiples workflows n8n** | Separar file_watcher (detección) de process_document (procesamiento) permite reutilización |
| **OCR en PPTX** | Tesseract con idioma español para extraer texto de diapositivas con imágenes |
| **Audio PCM→WAV→MP3** | Gemini devuelve PCM raw 24kHz; se envuelve en WAV con `wave` module, luego se comprime a MP3 con pydub+ffmpeg |
| **CSS variables sin blue** | Tema estrictamente monocromático: blanco puro / negro puro / grises neutros. Sin tonos azules o slate |
| **Cascade delete en carpetas** | Al eliminar carpeta monitoreada, se borran todos sus documentos (PostgreSQL + Qdrant chunks) automáticamente |
| **Single-user, sin auth** | Diseñado para uso personal local; no hay rutas de autenticación ni sesiones |

---

## Flujo de Procesamiento Automático

```
1. Usuario arrastra archivo a carpeta monitoreada
       │
2. watcher_host.py (host-side) detecta con watchdog
       │
3. POST a n8n webhook (http://localhost:5678/webhook/file-watcher)
       │
4. n8n workflow activado → llama a /api/documents/process
       │
5. Backend:
   a. Calcula hash SHA-256 (evita duplicados)
   b. Extrae texto (con OCR si PPTX con imágenes)
   c. Divide en chunks con overlap
   d. Genera embeddings con fastembed
   e. Almacena en Qdrant
   f. Dispara workflow n8n de procesamiento asíncrono
   g. Marca documento como "processed"
       │
6. Frontend: al recargar, el documento aparece en la lista
```

---

## Próximas Mejoras Potenciales

- Chat persistente por documento (historial asociado a `document_id`)
- Búsqueda global de texto en todos los documentos
- Exportar flashcards y quizzes a PDF/Anki
- Repetición espaciada para flashcards
- Preview de documentos en el frontend
- Mezcla de voces en podcasts (una voz por presentador)
- Más idiomas para podcasts
- Progreso visual durante generación de contenido
