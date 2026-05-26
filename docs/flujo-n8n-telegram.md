# n8n + Telegram: Automatización del Asistente de Estudio

## 1. Arquitectura General

```
                    ┌──────────────────────────────────────────────┐
                    │          INTERNET / USUARIO                   │
                    │   (Telegram App en celular / escritorio)      │
                    └──────────────────────┬───────────────────────┘
                                           │  Envía mensaje de texto
                                           │  o comando
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │          Telegram Bot API                     │
                    │  (servidores de Telegram)                     │
                    └──────────────────────┬───────────────────────┘
                                           │  Polling cada 500ms
                                           │  (n8n pregunta: "¿hay
                                           │   nuevos mensajes?")
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │          n8n (Docker)                        │
                    │  Workflow: "Telegram Bot"                    │
                    │  Puerto: 5678                                 │
                    │                                              │
                    │  Telegram Trigger ─► Is Owner? ─► Route      │
                    │                              Command         │
                    │                                  │           │
                    │  ┌─── /start ────────► Send Welcome          │
                    │  ├─── /help ─────────► Send Help             │
                    │  ├─── /docs list ────► HTTP GET Backend      │
                    │  ├─── /docs folders ─► HTTP GET Backend      │
                    │  ├─── /podcast gen ──► HTTP POST Backend     │
                    │  ├─── /ask ──────────► HTTP POST Backend     │
                    │  ├─── /create docs ──► HTTP POST Backend     │
                    │  ├─── /create podcast► HTTP POST Backend     │
                    │  └─── (fallback) ────► Send Help             │
                    └──────────────────────┬───────────────────────┘
                                           │  HTTP (red interna Docker)
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │   Backend FastAPI (Python)                    │
                    │   study-backend:8000                          │
                    │                                              │
                    │  routers/ ──── services/                      │
                    │  ├─ documents.py  ├─ groq_service.py         │
                    │  ├─ chat.py       ├─ embeddings.py           │
                    │  ├─ monitor.py    ├─ vector_store.py         │
                    │  ├─ podcasts.py   ├─ podcast_service.py      │
                    │  ├─ content.py    ├─ content_generator.py    │
                    │  └─ create.py     └─ extractor.py            │
                    └────┬──────┬──────┬───────────────────────────┘
                         │      │      │
                    ┌────┘      │      └─────┐
                    ▼           ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │PostgreSQL│ │  Qdrant  │ │   APIs   │
              │ (datos   │ │(vectores)│ │ Externas  │
              │  relac.) │ │          │ │ Groq     │
              │          │ │          │ │ Gemini   │
              └──────────┘ └──────────┘ └──────────┘
```

## 2. Componentes del Sistema

### 2.1 n8n (Workflow Automation)

n8n es el **orquestador**. Su función es:
- Recibir mensajes de Telegram (via polling)
- Decidir qué hacer con cada mensaje (switch/router)
- Llamar al backend cuando sea necesario (HTTP Request)
- Enviar respuestas al usuario (Telegram sendMessage/sendAudio)

### 2.2 Backend FastAPI (Python)

API REST que contiene toda la **lógica de negocio**:
- Procesamiento de documentos (extraer texto, crear embeddings)
- Chat RAG (búsqueda vectorial + Groq LLM)
- Generación de podcasts (script con Groq + audio con Gemini TTS)
- Generación de contenido educativo (Groq)
- Monitoreo de carpetas (watchdog)

### 2.3 PostgreSQL

Base de datos relacional que almacena:
- Documentos, carpetas monitoreadas
- Mensajes de chat
- Podcasts generados
- Resúmenes, flashcards, quizzes

### 2.4 Qdrant

Base de datos vectorial. Almacena los **embeddings** (representaciones numéricas) de los fragmentos de documentos. Permite búsqueda semántica.

### 2.5 Groq LLM

Proveedor de modelos de lenguaje. Se usa para:
- Responder preguntas en el chat RAG
- Generar resúmenes, flashcards, quizzes
- Escribir guiones de podcasts
- Crear documentos educativos desde cero

### 2.6 Gemini TTS (Google)

Convierte texto a voz. Toma el guión del podcast y genera un archivo de audio MP3.

### 2.7 ngrok

Túnel HTTPS público que expone n8n a internet (necesario para que Telegram pueda enviar webhooks, aunque actualmente el bot usa polling).

---

## 3. Flujo Completo del Bot de Telegram

### 3.1 Diagrama de Nodos (n8n Workflow)

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
                         (sigue)       │  (SIN CONEXIÓN)
                                    ▼
                              (mensaje
                              ignorado)
                                   
                         ┌─────────────────────┐
                         │    Route Command     │
                         │  (Switch con 10      │
                         │   reglas + fallback) │
                         └──┬──┬──┬──┬──┬──┬──┐
                            │  │  │  │  │  │  │
         ┌──────────────────┘  │  │  │  │  │  └──────────────┐
         │     ┌────────────────┘  │  │  │  └───────┐        │
         │     │     ┌─────────────┘  │  └────┐      │        │
         │     │     │     ┌──────────┘       │      │        │
         ▼     ▼     ▼     ▼         ▼        ▼      ▼        ▼
       [0]    [1]   [2]   [3]      [4][5]    [6]    [7]   [8][9]  [10]
      Send   Send  Extract Extract Send   Prep.  Send   Ext.   Send
     Welcome Help Docs   Folders Gen    Chat   Pod.   Docs/  Help
                   Params Params        Body   Help   Pod.  (fallback)
                      │       │          │             Topic
                      ▼       ▼          ▼               │
                  List     List       Chat        ┌──────┴──────┐
                 Docs    Folders      Ask         │              │
                      │       │          │        ▼              ▼
                      ▼       ▼          ▼     Create         Create
                 Format   Format      Send     Docs           Podcast
                  Docs    Folders    Answer       │              │
                      │       │                   ▼              ▼
                      ▼       ▼               Send          Download
                 Send      Send            Create           Audio
                 Docs      Folders        Confirm              │
                 List      List                               ▼
                                                     Send Audio Direct
```

### 3.2 Paso a Paso del Procesamiento

#### Paso 1: Telegram Trigger

```
Tipo: n8n-nodes-base.telegramTrigger
Configuración: polling = true, pollingInterval = 500ms
Salida: $json.message (texto, chat_id, fecha, etc.)
```

El trigger hace **polling** cada 500ms a la API de Telegram preguntando: "¿Hay mensajes nuevos?". Cuando encuentra uno, lo pasa al siguiente nodo.

#### Paso 2: Is Owner? (Autorización)

```
Tipo: n8n-nodes-base.if
Condición: $json.message.chat.id == $env.TELEGRAM_OWNER_ID
```

Filtro de seguridad. Solo el dueño (chat ID: 6732301888) puede usar el bot. Si alguien más escribe, el mensaje se ignora silenciosamente (la rama "false" no tiene conexiones).

#### Paso 3: Route Command (Enrutador)

```
Tipo: n8n-nodes-base.switch (modo: rules)
```

El mensaje se pasa a minúsculas y se compara contra 10 reglas en orden:

| Índice | Regla | Tipo | Comando |
|--------|-------|------|---------|
| 0 | empieza con "/start" | startsWith | Bienvenida |
| 1 | empieza con "/help" | startsWith | Ayuda |
| 2 | regex: ^/docs list | regex | Listar docs |
| 3 | regex: ^/docs folders | regex | Listar carpetas |
| 4 | regex: ^/podcast gen(?:erate)? \d+ | regex | Podcast por ID |
| 5 | regex: ^/podcast gen_folder | regex | Podcast por carpeta |
| 6 | empieza con "/ask" | startsWith | Preguntar (RAG) |
| 7 | empieza con "/podcast" | startsWith | Ayuda de podcast |
| 8 | regex: ^/create docs | regex | Crear documento |
| 9 | regex: ^/create podcast | regex | Crear podcast |
| 10 | fallback | — | Mostrar ayuda |

**Nota importante:** Las reglas más específicas (regex, con índice bajo) se evalúan primero. Por ejemplo, `/podcast gen 123` coincide con la regla 4 (específica), no con la regla 7 (genérica `/podcast`).

---

## 4. Flujo de Cada Comando

### 4.1 /start → Mensaje de Bienvenida

```
Usuario: /start
  → Route Command [0] → Send Welcome
  → Respuesta: "🎓 Bienvenido a StudiedUp..."
```

Camino directo. Un solo nodo envía el mensaje de bienvenida.

### 4.2 /help → Lista de Comandos

```
Usuario: /help
  → Route Command [1] → Send Help
  → Respuesta: Lista completa de comandos con ejemplos
```

Idem. Envía la lista de comandos disponibles.

### 4.3 /docs list [página] → Documentos

```
Usuario: /docs list 2
  → Route Command [2] → Extract Docs Params
     ↑ Extrae el número de página (default: 1, page_size: 10)
  → List Documents
     ↑ HTTP GET http://backend:8000/api/documents?page=2&page_size=10
     ↑ Respuesta: { items: [...], total: 25, page: 2, page_size: 10 }
  → Format Docs List
     ↑ Convierte JSON a HTML formateado
     ↑ Ej: "<b>1.</b> documento.pdf | <i>procesado</i>"
  → Send Docs List
     ↑ Envía el HTML al chat
```

**¿Qué pasa en el backend?**
- Consulta PostgreSQL: `SELECT * FROM documents ORDER BY created_at DESC LIMIT 10 OFFSET 10`
- Devuelve los documentos con paginación

### 4.4 /docs folders [página] → Carpetas

```
Usuario: /docs folders 1
  → Route Command [3] → Extract Folders Params
     ↑ Extrae página (default: 1, page_size: 10)
  → List Folders
     ↑ HTTP GET http://backend:8000/api/monitor/folders?page=1&page_size=10
  → Format Folders List
  → Send Folders List
```

Misma lógica que /docs list pero para carpetas monitoreadas.

### 4.5 /podcast gen <ID> → Podcast de un documento

```
Usuario: /podcast gen 5
  → Route Command [4] → Send Generating
     ↑ Responde: "🎙️ Generando podcast... ⏳"
  → Extract Doc ID
     ↑ Extrae el número 5 del comando
  → Generate Podcast
     ↑ HTTP POST http://backend:8000/api/podcasts/by-document/5
  → Download Audio
     ↑ HTTP GET http://backend:8000/api/podcasts/<id>/audio
     ↑ (arraybuffer → binary audio/mpeg)
  → Send Audio Direct
     ↑ HTTP POST https://api.telegram.org/bot<TOKEN>/sendAudio
     ↑ (multipart/form-data con chat_id + audio mp3)
```

**¿Qué pasa en el backend?**
1. Busca el documento ID=5 en PostgreSQL
2. Recupera todos los fragmentos de texto desde Qdrant
3. Envía el texto a **Groq** con un prompt que pide un guión conversacional entre dos hosts (HostA y HostB)
4. El guión resultante se envía a **Gemini TTS** para generar audio
5. El audio MP3 se guarda en `/app/podcasts/`
6. Devuelve el ID del podcast → n8n descarga el audio y lo envía a Telegram

### 4.6 /podcast gen_folder <ruta> → Podcast de carpeta

```
Usuario: /podcast gen_folder /home/daviuk/materias/redes
  → Route Command [5] → Send Generating Folder
  → Extract Folder Name
     ↑ Extrae: "/home/daviuk/materias/redes"
  → Generate Podcast by Folder
     ↑ HTTP POST http://backend:8000/api/podcasts/by-folder-path
     ↑ Body: { "folder_path": "/home/daviuk/materias/redes" }
  → Download Audio → Send Audio Direct
```

**¿Qué pasa en el backend?**
1. Busca todos los documentos procesados en esa ruta
2. Recupera los fragmentos de texto de todos ellos desde Qdrant
3. Genera guión con Groq y audio con Gemini TTS (igual que arriba)

### 4.7 /ask <pregunta> → Chat RAG

```
Usuario: /ask ¿Qué es el modelo OSI?
  → Route Command [6] → Prepare Chat Body
     ↑ Extrae: "¿Qué es el modelo OSI?"
  → Chat Ask
     ↑ HTTP POST http://backend:8000/api/chat/ask
     ↑ Body: { "message": "¿Qué es el modelo OSI?" }
  → Send Answer
     ↑ Envía la respuesta al chat
```

**¿Qué pasa en el backend? (RAG - Retrieval Augmented Generation)**

```
Pregunta: "¿Qué es el modelo OSI?"
         │
         ▼
  ┌──────────────┐
  │  Embeddings   │  Convierte la pregunta en un vector
  │  (FastEmbed)  │  (384 dimensiones)
  └──────┬───────┘
         │ vector de la pregunta
         ▼
  ┌──────────────┐
  │   Qdrant     │  Búsqueda de similitud coseno
  │ (vector DB)  │  Encuentra los 20 fragmentos más relevantes
  └──────┬───────┘
         │ fragmentos de texto similares
         ▼
  ┌──────────────┐
  │   Groq LLM   │  Prompt: "Contexto: [fragmentos]...
  │  (llama-3.1) │  Pregunta: ¿Qué es el modelo OSI?
  └──────┬───────┘  Responde en español..."
         │ respuesta + fuentes
         ▼
  ┌──────────────┐
  │  PostgreSQL   │  Guarda pregunta, respuesta y fuentes
  │              │  en tabla chat_messages
  └──────────────┘
         │
         ▼
  Respuesta al usuario
```

### 4.8 /create docs <tema> → Crear documento educativo

```
Usuario: /create docs seguridad informática
  → Route Command [8] → Extract Create Docs Topic
     ↑ Extrae: "seguridad informática"
  → Create Docs
     ↑ HTTP POST http://backend:8000/api/create/docs
     ↑ Body: { "topic": "seguridad informática" }
  → Send Create Confirm
     ↑ Responde con ID del documento y ruta
```

**¿Qué pasa en el backend?**

```
Tema: "seguridad informática"
         │
         ▼
  ┌──────────────┐
  │   Groq LLM   │  Prompt: "Genera un documento educativo
  │              │  en markdown de 1500+ palabras sobre
  │              │  seguridad informática. Incluye:
  │              │  introducción, conceptos, desarrollo,
  │              │  ejemplos, conclusión."
  └──────┬───────┘
         │ documento markdown
         ▼
  ┌──────────────┐
  │   Guardar    │  /documents/created/seguridad-informatica/
  │   archivo    │  seguridad-informatica.md
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │   Chunkear   │  Divide el markdown en fragmentos
  │              │  de ~500 caracteres
  └──────┬───────┘
         │ fragmentos
         ▼
  ┌──────────────┐
  │  Embeddings  │  Convierte cada fragmento a vector
  │  + Qdrant    │  y los almacena para búsqueda futura
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  PostgreSQL  │  Crea registro del documento
  └──────────────┘
         │
         ▼
  Respuesta: "Documento creado. ID: 42, ruta: ..."
```

### 4.9 /create podcast <tema> → Crear podcast desde cero

```
Usuario: /create podcast ISO 27001
  → Route Command [9] → Extract Create Podcast Topic
     ↑ Extrae: "ISO 27001"
  → Create Podcast
     ↑ HTTP POST http://backend:8000/api/create/podcast
     ↑ Body: { "topic": "ISO 27001" }
  → Download Audio → Send Audio Direct
```

**¿Qué pasa en el backend?**
1. Genera el documento educativo (igual que /create docs)
2. Toma el texto generado como fuente
3. Genera guión de podcast con Groq
4. Sintetiza audio con Gemini TTS
5. Devuelve el podcast → n8n descarga y envía el MP3

### 4.10 Fallback (comando no reconocido)

```
Usuario: /algoquenoexiste
  → Route Command [10] (fallback) → Send Help
  → Respuesta: Lista de comandos disponibles
```

Cualquier mensaje que no coincida con ninguna regla recibe la ayuda general.

---

## 5. ¿Qué Automatiza n8n Exactamente?

n8n automatiza el **flujo completo de interacción** entre el usuario (Telegram) y los servicios backend:

### 5.1 Lo que n8n **hace**:

1. **Escucha mensajes** de Telegram cada 500ms (polling)
2. **Autoriza** al usuario (filtro de chat ID)
3. **Enruta** cada comando al procesador correcto
4. **Formatea respuestas** (convierte JSON a HTML legible)
5. **Envía respuestas** de vuelta a Telegram (texto y audio)
6. **Maneja paginación** (extrae números de página de los comandos)
7. **Descarga archivos de audio** del backend y los reenvía a Telegram
8. **Provee fallback** para comandos no reconocidos

### 5.2 Lo que n8n **NO** hace (delega al backend):

1. **No procesa documentos** (extracción de texto, embeddings)
2. **No genera contenido** (ni respuestas, ni guiones, ni audio)
3. **No busca en la base de datos** vectorial
4. **No llama a APIs externas** (Groq, Gemini)
5. **No monitorea carpetas** del sistema de archivos

### 5.3 Resumen mental

> n8n es el **recepcionista** que recibe los pedidos del usuario y los pasa al **equipo técnico** (backend). El backend hace el trabajo pesado y devuelve los resultados. n8n los formatea bonito y se los entrega al usuario.

---

## 6. Infraestructura (Docker Compose)

Todos los servicios corren en Docker en una red compartida `study-net`:

| Servicio | Puerto | Propósito |
|----------|--------|-----------|
| **n8n** | 5678 | Workflow automation |
| **backend** | 8000 | API FastAPI (Python) |
| **postgres** | 5433 | Base de datos relacional |
| **qdrant** | 6333 | Base de datos vectorial |
| **ngrok** | — | Túnel HTTPS público |

Comunicación entre servicios:

```
n8n ──HTTP──► backend (http://backend:8000/api/...)
backend ──SQL──► postgres (postgres:5432)
backend ──gRPC──► qdrant (qdrant:6333)
backend ──HTTP──► Groq API (api.groq.com)
backend ──HTTP──► Gemini API (generativelanguage.googleapis.com)
```

---

## 7. Variables de Entorno Clave (`.env`)

| Variable | Uso |
|----------|-----|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram |
| `TELEGRAM_OWNER_ID` | Chat ID del dueño (único autorizado) |
| `GROQ_API_KEY` | API key para Groq LLM |
| `GOOGLE_API_KEY` | API key para Gemini TTS |
| `GROQ_CHAT_MODEL` | Modelo de lenguaje (default: llama-3.1-8b-instant) |
| `EMBEDDING_MODEL` | Modelo de embeddings (multilingual) |
| `TTS_MODEL` | Modelo de texto-a-voz |

---

## 8. Resumen Visual del Flujo Completo

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ USUARIO  │───►│ TELEGRAM │───►│   n8n    │───►│ BACKEND  │
│ Telegram │    │   API    │    │ (router) │    │(FastAPI) │
│   App    │    │          │    │          │    │          │
│          │    │          │    │ /start   │    │ /api/    │
│ /docs    │    │          │    │ /help    │    │ documents│
│ /ask     │    │          │    │ /docs    │    │ /api/    │
│ /podcast │    │          │    │ /podcast │    │ podcasts │
│ /create  │    │          │    │ /create  │    │ /api/    │
│          │    │          │    │          │    │ chat     │
│          │◄───│──────────│────│──────────│────│ /api/    │
│          │    │          │    │ (formatea│    │ create   │
│          │    │          │    │  y envía)│    │          │
│          │    │          │    │          │    ├──────────┤
│          │    │          │    │          │    │ PostgreSQL│
│          │    │          │    │          │    │  Qdrant   │
│          │    │          │    │          │    │  Groq API │
│          │    │          │    │          │    │ Gemini TTS│
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## 9. Glosario

| Término | Significado |
|---------|-------------|
| **n8n** | Plataforma de automatización de workflows (similar a Node-RED) |
| **Trigger** | Nodo que inicia el flujo (en este caso, polling de Telegram) |
| **Polling** | El bot pregunta periódicamente si hay nuevos mensajes |
| **Switch** | Nodo que enruta según condiciones (como un if/else) |
| **Code Node** | Nodo que ejecuta código JavaScript |
| **HTTP Request** | Nodo que hace llamadas HTTP (GET, POST) |
| **RAG** | Retrieval Augmented Generation: busca información relevante y se la pasa al LLM para responder |
| **Embedding** | Vector numérico que representa el significado de un texto |
| **Qdrant** | Base de datos que guarda y busca vectores por similitud |
| **Groq** | Proveedor de modelos de lenguaje (LLM) |
| **Gemini TTS** | Servicio de Google que convierte texto a voz |
| **Endpoint** | URL de una API (ej: /api/create/docs) |
