#!/bin/bash

echo "===================================="
echo "  Setup Telegram Bot en n8n"
echo "===================================="
echo ""

# 1. Verificar n8n
echo "⏳ Verificando que n8n esté disponible..."
if ! docker exec study-n8n n8n --version &>/dev/null 2>&1; then
  echo "❌ n8n no está corriendo. Ejecuta: docker compose up -d"
  exit 1
fi
echo "✅ n8n está disponible"

# 2. Obtener userId y projectId desde la BD
echo "👤 Obteniendo IDs de usuario..."
IDS=$(docker exec study-n8n node -e "
const { DatabaseSync } = require('node:sqlite');
const db = new DatabaseSync('/home/node/.n8n/database.sqlite');
const user = db.prepare('SELECT id FROM user LIMIT 1').get();
const project = db.prepare(\"SELECT id FROM project WHERE type='personal' LIMIT 1\").get();
console.log(JSON.stringify({ userId: user?.id, projectId: project?.id }));
db.close();
")

OWNER_ID=$(echo "$IDS" | node -e "process.stdin.on('data',d=>{const j=JSON.parse(d);console.log(j.userId)})")
PROJECT_ID=$(echo "$IDS" | node -e "process.stdin.on('data',d=>{const j=JSON.parse(d);console.log(j.projectId)})")

if [ -z "$OWNER_ID" ] || [ -z "$PROJECT_ID" ]; then
  echo "❌ No se encontró usuario/proyecto. Abre http://localhost:5678 y crea una cuenta."
  exit 1
fi
echo "✅ Owner ID: $OWNER_ID"
echo "✅ Project ID: $PROJECT_ID"

# 3. Importar credencial de Telegram (si no existe)
echo "🔑 Importando credencial de Telegram..."
docker cp "$(dirname "$0")/workflows/telegram_credential.json" study-n8n:/tmp/telegram_credential.json
if docker exec study-n8n n8n import:credentials \
  --input=/tmp/telegram_credential.json --userId="$OWNER_ID" 2>&1; then
  echo "✅ Credencial importada"
else
  echo "⚠️  (puede que ya exista, continuamos...)"
fi

# 4. Insertar workflow directo en la BD
echo "📦 Insertando workflow 'Telegram Bot' en la BD..."
docker cp "$(dirname "$0")/workflows/telegram_bot.json" study-n8n:/tmp/telegram_bot.json

docker exec study-n8n node -e "
const crypto = require('crypto');
const fs = require('fs');
const { DatabaseSync } = require('node:sqlite');

const db = new DatabaseSync('/home/node/.n8n/database.sqlite');

// Leer workflow JSON
const raw = fs.readFileSync('/tmp/telegram_bot.json', 'utf8');
const workflow = JSON.parse(raw)[0];

const wfId = crypto.randomUUID();
const now = new Date().toISOString().replace('Z', '').substring(0, 23);
const versionId = crypto.randomUUID();

// Insertar en workflow_entity
const insert = db.prepare(\`
  INSERT INTO workflow_entity 
    (id, name, active, nodes, connections, settings, staticData, pinData, 
     versionId, triggerCount, meta, createdAt, updatedAt, isArchived, 
     versionCounter, description)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 0, 1, ?)
\`);

insert.run(
  wfId,
  workflow.name,
  0,  // active = false
  JSON.stringify(workflow.nodes),
  JSON.stringify(workflow.connections),
  JSON.stringify(workflow.settings || { executionOrder: 'v1' }),
  null,  // staticData
  null,  // pinData
  versionId,
  null,  // meta
  now,   // createdAt
  now,   // updatedAt
  null   // description
);

// Insertar en shared_workflow (ownership)
const insertSw = db.prepare(\`
  INSERT INTO shared_workflow 
    (workflowId, projectId, role, createdAt, updatedAt)
  VALUES (?, ?, ?, ?, ?)
\`);
insertSw.run(wfId, '$PROJECT_ID', 'workflow:owner', now, now);

console.log('Workflow ID:', wfId);
db.close();
"

echo "✅ Workflow insertado en la BD"
echo ""

echo "===================================="
echo "  ✅ SETUP COMPLETADO"
echo "===================================="
echo ""
echo "  1. Abre http://localhost:5678"
echo "  2. Verás 'Telegram Bot' en la lista de workflows"
echo "  3. Ábrelo y vincular la credencial en cada nodo Telegram:"
echo "     - Telegram Trigger"
echo "     - Send Welcome"
echo "     - Send Help"
echo "     - Send Docs List"
echo "     - Send Generating"
echo "     - Send Podcast Help"
echo "     - Send Answer"
echo "     - Send Audio"
echo "     (En cada nodo, selecciona 'Telegram Bot' del dropdown)"
echo ""
echo "  4. Actívalo con el toggle ▶️"
echo "  5. Habla con @studied_up_bot en Telegram"
echo ""
echo "💡 Si la credencial no aparece en el dropdown:"
echo "   Settings → Credentials → 'Telegram Bot' ya debería estar ahí"
echo ""
