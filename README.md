# Study Assistant — Asistente de Estudio Académico

Asistente de estudio personal con procesamiento automatizado de documentos, chat con RAG (Retrieval-Augmented Generation), generación de contenido educativo vía IA, y podcasts educativos. Todo orquestado con **n8n** y accesible desde **Telegram**.

```
                    ┌──────────────────────────────────────────────┐
                    │          USUARIO (Telegram App)               │
                    │   Celular / Desktop / Web                     │
                    └──────────────────────┬───────────────────────┘
                                           │  /docs list, /ask, /podcast gen
                                           │  /create docs, /create podcast
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │         n8n (Workflow Automation)             │
                    │  Telegram Trigger → Is Owner? → Route Command │
                    │                                              │
                    │  10 rutas: welcome, help, docs, folders,     │
                    │  podcast (gen + gen_folder), ask (RAG),      │
                    │  create (docs + podcast), fallback           │
                    └──────────────────────┬───────────────────────┘
                                           │ HTTP (red interna Docker)
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │   Backend FastAPI (Python 3.12)               │
                    │   study-backend:8000                          │
                    │                                              │
                    │  routers/ ──── services/                      │
                    │  ├─ documents  ├─ groq_service (Groq LLM)    │
                    │  ├─ chat       ├─ embeddings (fastembed)     │
                    │  ├─ monitor    ├─ vector_store (Qdrant)      │
                    │  ├─ podcasts   ├─ podcast_service (TTS)      │
                    │  ├─ content    ├─ content_generator          │
                    │  └─ create     └─ extractor / chunker        │
                    └────┬──────┬──────┬───────────────────────────┘
                         │      │      │
                    ┌────┘      │      └─────┐
                    ▼           ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │PostgreSQL│ │  Qdrant  │ │   APIs   │
              │ (datos   │ │(vectores)│ │ Externas  │
              │  relac.) │ │ 384-dim  │ │ Groq     │
              │          │ │ coseno   │ │ Gemini   │
              └──────────┘ └──────────┘ └──────────┘
```

---

## Arquitectura General

El sistema consta de **5 servicios Docker** en una red bridge `study-net`:

| Servicio   | Puerto | Propósito |
|------------|--------|-----------|
| **n8n**    | 5678   | Orquestación visual de workflows |
| **backend**| 8000   | API FastAPI con toda la lógica de negocio |
| **postgres**| 5433  | Base de datos relacional (documentos, chats, podcasts) |
| **qdrant** | 6333   | Base de datos vectorial (embeddings semánticos) |
| **ngrok**  | —      | Túnel HTTPS público a n8n |

**Comunicación entre servicios:**
- `n8n ──HTTP──► backend` (http://backend:8000/api/...)
- `backend ──SQL──► postgres` (postgres:5432)
- `backend ──gRPC──► qdrant` (qdrant:6333)
- `backend ──HTTP──► Groq API` (api.groq.com)
- `backend ──HTTP──► Gemini TTS` (generativelanguage.googleapis.com)

### Stack Tecnológico

| Componente       | Tecnología |
|------------------|------------|
| Orquestación     | n8n 2.21.4 (Self Hosted) |
| API Backend      | FastAPI (Python 3.12) |
| ORM              | SQLAlchemy 2.0 |
| Base de datos    | PostgreSQL 16 (Alpine) |
| Vector Store     | Qdrant v1.18 |
| Embeddings       | fastembed 0.3.3 (local, offline, 384-dim, multilingüe) |
| LLM              | Groq API (`llama-3.1-8b-instant`, configurable) |
| TTS              | Google Gemini (`gemini-2.5-flash-preview-tts`, configurable) |
| OCR              | Tesseract + pdf2image (español, para PPTX con imágenes) |
| Extracción       | pdfplumber, python-pptx, python-docx |
| Audio            | pydub + ffmpeg (PCM → WAV → MP3) |
| Túnel HTTPS      | ngrok (dominio fijo gratuito) |
| Contenedores     | Docker Compose |

---

## Componentes del Sistema

### n8n — Orquestador de Workflows

n8n actúa como el **router** entre el usuario (Telegram) y el backend. Su función es:

- **Recibir mensajes** de Telegram vía polling cada 500ms
- **Autorizar** al usuario (filtro por chat ID del dueño)
- **Enrutar** cada comando al procesador correcto (switch con 10 reglas)
- **Formatear respuestas** (convierte JSON a HTML)
- **Enviar respuestas** de vuelta a Telegram (texto y audio MP3)
- **Descargar archivos** de audio del backend y reenviarlos a Telegram
- **Manejar paginación** (extrae números de página de los comandos)

n8n **no** procesa documentos, ni genera contenido, ni busca en la BD vectorial — delega todo eso al backend.

### Backend FastAPI — Lógica de Negocio

API REST con todos los servicios de procesamiento:

- **Documentos**: extracción de texto (PDF/PPTX/DOCX/MD/TXT), chunking, embeddings, almacenamiento vectorial
- **Chat RAG**: búsqueda semántica en Qdrant + Groq LLM para responder preguntas con contexto
- **Podcasts**: generación de guiones conversacionales (Groq) + síntesis de voz (Gemini TTS)
- **Contenido educativo**: creación automática de documentos markdown sobre cualquier tema (Groq)
- **Monitoreo**: watchdog de carpetas para procesamiento automático de archivos nuevos

### PostgreSQL — Datos Relacionales

Almacena: documentos, carpetas monitoreadas, mensajes de chat, podcasts, resúmenes, flashcards, quizzes.

### Qdrant — Base de Datos Vectorial

Almacena **embeddings** (vectores de 384 dimensiones) de fragmentos de documentos. Permite búsqueda semántica por similitud coseno.

### Groq — LLM

Se usa para:
- Responder preguntas en el chat RAG
- Generar resúmenes, flashcards, quizzes
- Escribir guiones de podcasts (formato conversacional HostA/HostB)
- Crear documentos educativos desde cero

### Gemini TTS — Texto a Voz

Toma el guión del podcast y genera audio MP3 con voz natural (modelo `gemini-2.5-flash-preview-tts`).

### ngrok — Túnel HTTPS

Expone n8n a internet con dominio fijo para que Telegram pueda enviar webhooks. Actualmente el bot usa **polling** (n8n consulta activamente), por lo que ngrok es opcional para el funcionamiento básico.

---

## Flujo del Bot de Telegram

### Diagrama de Nodos (30 nodos en total)

```
                         ┌─────────────────────┐
                         │   Telegram Trigger   │
                         │  (polling c/500ms)  │
                         └──────────┬──────────┘
                                    │ $json.message
                                    ▼
                         ┌─────────────────────┐
                         │     Is Owner?        │
                         │ chat.id == OWNER_ID? │
                         └────┬────────┬───────┘
                         Sí   │        │  No
                              │        │  (mensaje ignorado)
                              ▼
                         ┌─────────────────────┐
                         │    Route Command     │
                         │  (Switch, 10 reglas  │
                         │   + fallback)        │
                         └──┬──┬──┬──┬──┬──┬──┐
                            │  │  │  │  │  │  │
        ┌───────────────────┘  │  │  │  │  │  └────────────┐
        │   ┌──────────────────┘  │  │  │  └──────┐        │
        │   │   ┌─────────────────┘  │  └───┐     │        │
        │   │   │   ┌────────────────┘      │     │        │
        ▼   ▼   ▼   ▼         ▼       ▼     ▼     ▼        ▼
      [0]  [1] [2] [3]     [4][5]   [6]    [7]  [8][9]   [10]
     Send Send Ext. Ext.   Send    Prep.  Send  Ext.    Send
    Welco Help Docs Fol.   Gen.    Chat   Pod.  Docs/   Help
                 Params P.         Body   Help  Pod.   (fallback)
                  │      │          │            Topic
                  ▼      ▼          ▼              │
               List   List       Chat       ┌──────┴──────┐
              Docs   Folders     Ask        │              │
                  │      │        │         ▼              ▼
                  ▼      ▼        ▼      Create         Create
             Format  Format    Send      Docs           Podcast
              Docs   Folders  Answer        │              │
                  │      │                   ▼              ▼
                  ▼      ▼               Send          Download
             Send     Send             Create           Audio
             Docs    Folders          Confirm              │
             List    List                                 ▼
                                                  Send Audio Direct
```

### Reglas del Enrutador (Route Command)

| Índice | Regla | Tipo | Comando | Acción |
|--------|-------|------|---------|--------|
| 0 | empieza con `/start` | startsWith | Bienvenida | Send Welcome |
| 1 | empieza con `/help` | startsWith | Ayuda | Send Help |
| 2 | `^/docs list` | regex | Listar docs | HTTP GET `/api/documents` |
| 3 | `^/docs folders` | regex | Listar carpetas | HTTP GET `/api/monitor/folders` |
| 4 | `^/podcast gen(?:erate)? \d+` | regex | Podcast por ID | HTTP POST `/api/podcasts/by-document/{id}` |
| 5 | `^/podcast gen_folder` | regex | Podcast por carpeta | HTTP POST `/api/podcasts/by-folder-path` |
| 6 | empieza con `/ask` | startsWith | Pregunta RAG | HTTP POST `/api/chat/ask` |
| 7 | empieza con `/podcast` | startsWith | Ayuda podcast | Send Podcast Help |
| 8 | `^/create docs` | regex | Crear documento | HTTP POST `/api/create/docs` |
| 9 | `^/create podcast` | regex | Crear podcast | HTTP POST `/api/create/podcast` |
| 10 | fallback | — | No reconocido | Send Help |

### Flujo de Cada Comando

#### `/start` → Mensaje de Bienvenida

```
Usuario: /start
  → Route Command [0] → Send Welcome
  → "🎓 ¡Bienvenido a StudiedUp!..."
```

#### `/help` → Lista de Comandos

```
Usuario: /help
  → Route Command [1] → Send Help
  → Lista completa con ejemplos
```

#### `/docs list [página]` → Documentos Disponibles

```
Usuario: /docs list 2
  → Route Command [2] → Extract Docs Params
     Extrae página (default: 1, page_size: 10)
  → List Documents
     HTTP GET http://backend:8000/api/documents?page=2&page_size=10
  → Format Docs List (convierte JSON a HTML)
  → Send Docs List
```

**Backend**: Consulta PostgreSQL con paginación (`LIMIT 10 OFFSET 10`). Devuelve `{items[], total, page, page_size}`.

#### `/docs folders [página]` → Carpetas Monitoreadas

```
Usuario: /docs folders 1
  → Route Command [3] → Extract Folders Params
  → List Folders
     HTTP GET http://backend:8000/api/monitor/folders?page=1&page_size=10
  → Format Folders List → Send Folders List
```

#### `/podcast gen <ID>` → Podcast de un Documento

```
Usuario: /podcast gen 5
  → Route Command [4] → Send Generating ("🎙️ Generando podcast... ⏳")
  → Extract Doc ID (extrae el número 5)
  → Generate Podcast
     HTTP POST http://backend:8000/api/podcasts/by-document/5
  → Download Audio
     HTTP GET http://backend:8000/api/podcasts/<id>/audio (arraybuffer)
  → Send Audio Direct
     HTTP POST https://api.telegram.org/bot<TOKEN>/sendAudio (multipart)
```

**Backend**: Recupera fragmentos del documento desde Qdrant → Groq genera guión (HostA/HostB) → Gemini TTS sintetiza audio MP3 → Guarda en `/app/podcasts/`.

#### `/podcast gen_folder <ruta>` → Podcast de Carpeta

```
Usuario: /podcast gen_folder /home/daviuk/materias/redes
  → Route Command [5] → Send Generating Folder
  → Extract Folder Name → { folder_path: "/home/daviuk/materias/redes" }
  → Generate Podcast by Folder
     HTTP POST http://backend:8000/api/podcasts/by-folder-path
     Body: { "folder_path": "/home/daviuk/materias/redes" }
  → Download Audio → Send Audio Direct
```

**Backend**: Busca todos los documentos en esa ruta, combina sus textos, genera guión + audio.

#### `/ask <pregunta>` → Chat RAG

```
Usuario: /ask ¿Qué es el modelo OSI?
  → Route Command [6] → Prepare Chat Body
     Extrae: "¿Qué es el modelo OSI?"
  → Chat Ask
     HTTP POST http://backend:8000/api/chat/ask
     Body: { "message": "¿Qué es el modelo OSI?" }
  → Send Answer
```

**Backend (RAG)**:
```
Pregunta → fastembed (vector 384-dim)
         → Qdrant (búsqueda coseno, top 20 fragmentos)
         → Groq LLM (contexto + pregunta → respuesta)
         → PostgreSQL (guarda historial)
         → Respuesta al usuario
```

#### `/create docs <tema>` → Crear Documento con IA

```
Usuario: /create docs seguridad informática
  → Route Command [8] → Extract Create Docs Topic
     Extrae: "seguridad informática"
  → Create Docs
     HTTP POST http://backend:8000/api/create/docs
     Body: { "topic": "seguridad informática" }
  → Send Create Confirm
     "Documento creado. ID: 42, ruta: /documents/created/seguridad-informatica/..."
```

**Backend**: Groq genera documento markdown (1500+ palabras) → Guarda en `/documents/created/<slug>/` → Chunkea → Embeddings → Qdrant.

#### `/create podcast <tema>` → Crear Podcast con IA

```
Usuario: /create podcast ISO 27001
  → Route Command [9] → Extract Create Podcast Topic
  → Create Podcast
     HTTP POST http://backend:8000/api/create/podcast
     Body: { "topic": "ISO 27001" }
  → Download Audio → Send Audio Direct
```

**Backend**: Genera documento educativo → Usa ese texto como fuente → Genera guión (Groq) → Sintetiza audio (Gemini TTS) → Devuelve podcast.

#### Fallback → Ayuda General

```
Usuario: /cualquiercosanoexistente
  → Route Command [10] → Send Help
  → Lista de comandos disponibles
```

---

## API Endpoints — Backend

### Documentos (`/api/documents`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Listar documentos (query: `page`, `page_size`) |
| `GET` | `/{id}` | Obtener documento por ID |
| `POST` | `/process?filepath=` | Procesar archivo (extraer + chunk + embed + n8n) |
| `POST` | `/process-folder?folder_path=` | Procesar todos los archivos de una carpeta |
| `POST` | `/sync` | Sincronizar carpetas monitoreadas |
| `POST` | `/n8n-chunks` | Webhook para que n8n guarde chunks |
| `POST` | `/n8n-webhook` | Webhook alternativo para n8n |
| `DELETE` | `/{id}` | Eliminar documento + chunks vectoriales |

### Chat (`/api/chat`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/ask` | Pregunta RAG (body: `{ message }`) |
| `GET` | `/history` | Historial de mensajes |

### Monitor (`/api/monitor`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/folders` | Listar carpetas (query: `page`, `page_size`) |
| `POST` | `/folders` | Agregar carpeta (body: `{ path }`) |
| `DELETE` | `/folders` | Eliminar carpeta + cascade delete |

### Contenido (`/api/content`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST/GET` | `/summaries/{id}` | Generar/obtener resumen |
| `POST/GET` | `/flashcards/{id}` | Generar/obtener flashcards |
| `POST/GET` | `/quizzes/{id}` | Generar/obtener quiz |

### Podcasts (`/api/podcasts`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/by-document/{id}` | Generar podcast de un documento |
| `POST` | `/by-folder/{id}` | Generar podcast de carpeta monitoreada |
| `POST` | `/by-folder-path` | Generar podcast por ruta (body: `{ folder_path }`) |
| `GET` | `/` | Listar podcasts |
| `GET` | `/{id}/audio` | Descargar audio MP3 |
| `DELETE` | `/{id}` | Eliminar podcast + archivo |

### Creación con IA (`/api/create`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/docs` | Crear documento educativo (body: `{ topic }`) |
| `POST` | `/podcast` | Crear podcast desde cero (body: `{ topic }`) |

### Health

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/health` | `{"status":"ok","service":"study-assistant"}` |

---

## Estructura del Backend

```
backend/
├── Dockerfile
├── requirements.txt
├── watcher_host.py           # Script host-side para watchdog de carpetas
├── scripts/init_db.py        # Creación de tablas
├── podcasts/                 # Audios generados
└── app/
    ├── main.py               # FastAPI app + CORS + rutas
    ├── config.py             # Settings (Pydantic, desde .env)
    ├── database.py           # SQLAlchemy engine/session
    ├── schemas/schemas.py    # Pydantic request/response
    ├── models/
    │   ├── document.py       # Document, MonitoredFolder
    │   ├── chat.py           # ChatMessage
    │   ├── quiz.py           # Summary, Flashcard, Quiz
    │   └── podcast.py        # Podcast
    ├── routers/
    │   ├── documents.py      # CRUD docs, sync, process, webhooks n8n
    │   ├── chat.py           # /api/chat/ask (RAG), /history
    │   ├── monitor.py        # /api/monitor/folders (CRUD)
    │   ├── content.py        # /api/content/summaries, /flashcards, /quizzes
    │   ├── podcasts.py       # /api/podcasts (by-document, by-folder, audio)
    │   └── create.py         # /api/create/docs, /api/create/podcast
    └── services/
        ├── embeddings.py     # fastembed wrapper (singleton, offline)
        ├── vector_store.py   # Qdrant client (store, search, delete, scroll)
        ├── extractor.py      # PDF/PPTX/DOCX/TXT/MD → texto con OCR
        ├── chunker.py        # Texto → chunks ~500 chars con overlap
        ├── groq_service.py   # Groq API (chat, summary, quiz, flashcards)
        ├── podcast_service.py# Guión (Groq) + TTS (Gemini) → MP3
        ├── content_generator.py # Creación de documentos educativos con Groq
        ├── n8n_trigger.py    # HTTP call a webhook de n8n
        └── file_watcher.py   # watchdog observer (in-container)
```

---

## Pipeline de Datos

### Procesamiento de Documentos

```
Archivo (PDF/PPTX/DOCX/MD/TXT)
    │
    ▼
extract_text()
    ├── PDF: pdfplumber → texto por página
    ├── PPTX: python-pptx → texto slides + OCR imágenes (Tesseract español)
    ├── DOCX: python-docx → párrafos + tablas
    └── TXT/MD: lectura directa
    │
    ▼
chunk_document()
    ├── Divide en fragmentos de ~500 caracteres
    ├── Overlap de 50 caracteres
    └── Detecta saltos de página/diapositiva
    │
    ▼
vector_store.store_chunks()
    ├── fastembed → vector 384-dim por chunk
    └── Qdrant upsert con payload: document_id, filename, page, text
    │
    ▼
trigger_n8n_workflow()
    └── Webhook a n8n para procesamiento asíncrono
```

### Chat RAG

```
Pregunta del usuario
    │
    ▼
vector_store.search(query, top_k=20)
    ├── fastembed → vector 384-dim
    └── Qdrant búsqueda coseno → 20 fragmentos más relevantes
    │
    ▼
ask_groq(prompt con contexto + pregunta)
    ├── Groq llama-3.1-8b-instant
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
Seleccionar documento, carpeta, o tema nuevo
    │
    ▼
vector_store.get_document_texts(document_id)  [o contenido generado]
    │
    ├── Qdrant scroll filter por document_id
    └── Recupera todos los chunks de texto
    │
    ▼
generate_podcast_script(texts)
    ├── Groq genera guión conversacional (HostA + HostB)
    └── JSON con turns: [{speaker, text}, ...]
    │
    ▼
synthesize_audio(turns, podcast_id)
    ├── Gemini TTS (gemini-2.5-flash-preview-tts)
    │   POST generateContent con responseModalities: ["AUDIO"]
    │   Voz: "zephyr"
    ├── Decodifica PCM 24kHz 16-bit mono
    ├── Guarda como WAV
    ├── Convierte a MP3 con pydub + ffmpeg
    └── Duración real calculada
```

### Creación de Contenido con IA

```
Tema del usuario (ej: "seguridad informática")
    │
    ▼
content_generator.generate_document_content(topic)
    ├── Groq genera documento markdown (1500+ palabras)
    │   Prompt: título, introducción, conceptos, desarrollo, ejemplos, conclusión
    │   Tono: académico pero accesible
    │
    ▼
Guarda archivo en /documents/created/<slug>/<slug>.md
    │
    ▼
Chunk → Embeddings → Qdrant (misma pipeline que documentos)
    │
    ▼
Crea registro en PostgreSQL
```

---

## Infraestructura (Docker Compose)

```yaml
# docker-compose.yml — 5 servicios
services:
  postgres:   # PostgreSQL 16 Alpine, puerto 5433
  qdrant:     # Qdrant v1.18, puertos 6333/6334
  n8n:        # n8n latest, puerto 5678
  backend:    # FastAPI build local, puerto 8000
  ngrok:      # ngrok latest, túnel HTTPS
```

### Variables de Entorno (`.env`)

```env
# APIs
GROQ_API_KEY=gsk_tu_key
GOOGLE_API_KEY=AIza_tu_key
TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
TELEGRAM_OWNER_ID=123456789
NGROK_AUTHTOKEN=2abc123...
NGROK_DOMAIN=midominio.ngrok-free.dev

# Modelos (configurables)
GROQ_CHAT_MODEL=llama-3.1-8b-instant
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
TTS_MODEL=gemini-2.5-flash-preview-tts
```

**Nota:** Los modelos son completamente configurables. Cambia las variables en `.env` y recrea los contenedores con `docker compose up -d --force-recreate backend`.

---

## Configuración y Despliegue

### Prerequisitos

- Docker + Docker Compose
- API keys: Groq (https://console.groq.com), Google (https://aistudio.google.com), Telegram BotFather, ngrok

### Levantar el Proyecto

```bash
# 1. Clonar y configurar
cp .env.example .env   # Editar con tus API keys
mkdir -p documents podcasts

# 2. Iniciar servicios
docker compose up -d

# 3. Verificar estado
curl http://localhost:8000/api/health
# → {"status":"ok","service":"study-assistant"}

# 4. Importar workflow de Telegram en n8n
#    (http://localhost:5678 → Workflows → Import)
#    Archivo: workflows/telegram_bot.json

# 5. Asignar credencial "telegramApi" a cada nodo Telegram
#    (10 nodos: Trigger, Send Welcome, Send Help, etc.)

# 6. Activar workflow
```

### Servicios

| Servicio | Puerto | URL |
|----------|--------|-----|
| Backend  | 8000   | http://localhost:8000 |
| n8n      | 5678   | http://localhost:5678 |
| ngrok    | —      | https://{domain}.ngrok-free.dev |
| Qdrant   | 6333   | http://localhost:6333 |
| PostgreSQL | 5433 | postgresql://localhost:5433 |

### Comandos del Bot de Telegram

| Comando | Acción |
|---------|--------|
| `/start` | Mensaje de bienvenida |
| `/help` | Lista de comandos |
| `/docs list [página]` | Lista documentos (10 por página) |
| `/docs folders [página]` | Lista carpetas monitoreadas |
| `/podcast gen <ID>` | Genera podcast de un documento |
| `/podcast gen_folder <ruta>` | Genera podcast de una carpeta |
| `/ask <pregunta>` | Chat RAG con tus documentos |
| `/create docs <tema>` | Crea documento educativo con IA |
| `/create podcast <tema>` | Crea podcast desde cero con IA |

---

## ¿Qué Automatiza n8n?

### n8n HACE:

1. Escucha mensajes de Telegram cada 500ms (polling)
2. Autoriza al usuario (filtro por chat ID)
3. Enruta cada comando al procesador correcto
4. Formatea respuestas (JSON → HTML legible)
5. Envía respuestas de vuelta a Telegram (texto y audio)
6. Maneja paginación (extrae números de página)
7. Descarga archivos de audio del backend y los reenvía
8. Provee fallback para comandos no reconocidos

### n8n NO HACE (delega al backend):

1. No procesa documentos (extracción, embeddings)
2. No genera contenido (respuestas, guiones, audio)
3. No busca en la base de datos vectorial
4. No llama a APIs externas (Groq, Gemini)
5. No monitorea carpetas

> n8n es el **recepcionista** que recibe pedidos y los pasa al **equipo técnico** (backend).

---

## Decisiones Técnicas Clave

| Decisión | Razón |
|----------|-------|
| **Groq como LLM principal** | Rápido, estable, buena calidad académica. Gemini tuvo problemas de cuota (429). |
| **Gemini solo para TTS** | Alta calidad de voz, API con `responseModalities: ["AUDIO"]` y voces tipo estrella. |
| **fastembed local** | Embeddings offline, sin costos recurrentes, modelo multilingüe. |
| **384 dimensiones** | Balance entre velocidad y calidad semántica. |
| **PostgreSQL + Qdrant** | Split: metadata relacional en Postgres, vectores semánticos en Qdrant. |
| **Polling en Telegram** | n8n 2.21.4 permite polling nativo del trigger, sin depender de webhook externo. |
| **Filtro por chat ID** | Seguridad simple: solo el dueño (`TELEGRAM_OWNER_ID`) puede usar el bot. |
| **HTML parse_mode** | Todos los nodos Telegram usan `parse_mode: "HTML"` con escape de `<`, `>`, `&` en code nodes para evitar errores de entidad. |
| **Modelos configurables** | `GROQ_CHAT_MODEL`, `EMBEDDING_MODEL`, `TTS_MODEL` se ajustan en `.env` sin tocar código. |

---

## Archivos del Proyecto

| Archivo | Propósito |
|---------|-----------|
| `docker-compose.yml` | Infraestructura completa (5 servicios) |
| `.env` | Variables de entorno y API keys (gitignored) |
| `workflows/telegram_bot.json` | Workflow n8n del bot de Telegram (30 nodos) |
| `backend/app/` | Código fuente del backend FastAPI |
| `backend/app/routers/create.py` | Endpoints de creación con IA |
| `backend/app/services/content_generator.py` | Generación de contenido educativo con Groq |
| `backend/app/services/podcast_service.py` | Generación de guiones y síntesis de audio |
| `docs/flujo-n8n-telegram.md` | Documentación detallada del flujo n8n + Telegram |
| `postgres/init.sql` | Inicialización de base de datos |
| `setup_telegram_bot.sh` | Script de configuración del bot (legacy) |

---

## Glosario

| Término | Significado |
|---------|-------------|
| **n8n** | Plataforma de automatización de workflows visuales |
| **Trigger** | Nodo que inicia el flujo (polling de Telegram) |
| **Polling** | El bot pregunta periódicamente si hay nuevos mensajes |
| **Switch** | Nodo que enruta según condiciones (como if/else) |
| **Code Node** | Nodo que ejecuta código JavaScript en n8n |
| **HTTP Request** | Nodo que hace llamadas HTTP (GET, POST) |
| **RAG** | Retrieval Augmented Generation: busca información relevante y se la pasa al LLM |
| **Embedding** | Vector numérico (384-dim) que representa el significado de un texto |
| **Qdrant** | Base de datos vectorial para búsqueda semántica |
| **Groq** | Proveedor de modelos de lenguaje (LLM) ultrarrápido |
| **Gemini TTS** | Servicio de Google que convierte texto a voz natural |
| **Endpoint** | URL de una API (ej: `/api/create/docs`) |
