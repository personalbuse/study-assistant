import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import ChatWindow from './components/ChatWindow'
import DocumentList from './components/DocumentList'
import FolderPicker from './components/FolderPicker'
import Flashcards from './components/Flashcards'
import QuizViewer from './components/QuizViewer'
import api from './api/client'

export default function App() {
  const [activeView, setActiveView] = useState('dashboard')
  const [documents, setDocuments] = useState([])
  const [monitoredFolders, setMonitoredFolders] = useState([])
  const [syncing, setSyncing] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    loadDocuments()
    loadFolders()
  }, [])

  function toggleTheme() {
    setTheme(t => t === 'dark' ? 'light' : 'dark')
  }

  async function loadDocuments() {
    try {
      const res = await api.get('/documents')
      setDocuments(res.data)
    } catch (err) {
      console.error('Error loading documents:', err)
    }
  }

  async function loadFolders() {
    try {
      const res = await api.get('/monitor/folders')
      setMonitoredFolders(res.data.folders || [])
    } catch (err) {
      console.error('Error loading folders:', err)
    }
  }

  async function handleSelectFolder() {
    let folderPath = null

    if (window.electronAPI) {
      folderPath = await window.electronAPI.selectFolder()
    } else {
      folderPath = window.prompt('Ingresa la ruta completa de la carpeta a monitorear:')
    }

    if (!folderPath) return

    try {
      await api.post('/monitor/folders', { path: folderPath })
      loadFolders()
      loadDocuments()
    } catch (err) {
      const msg = err.response?.data?.detail || err.message
      alert('Error al agregar carpeta: ' + msg)
    }
  }

  async function handleSync() {
    setSyncing(true)
    try {
      const res = await api.post('/documents/sync')
      const data = res.data
      alert(
        `Sincronizacion completada\n\n` +
        `Agregados: ${data.total_added}\n` +
        `Eliminados: ${data.total_removed}\n` +
        (data.errors.length > 0 ? `Errores: ${data.total_errors}` : 'Sin errores')
      )
      loadDocuments()
      loadFolders()
    } catch (err) {
      console.error('Error syncing:', err)
      alert('Error al sincronizar: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="flex h-screen">
      <Sidebar
        activeView={activeView}
        onNavigate={setActiveView}
        folderCount={monitoredFolders.length}
        documentCount={documents.length}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <main className="flex-1 overflow-y-auto p-6">
        {activeView === 'dashboard' && (
          <Dashboard
            documents={documents}
            folders={monitoredFolders}
            onSelectFolder={handleSelectFolder}
          />
        )}

        {activeView === 'documents' && (
          <DocumentList documents={documents} onReload={loadDocuments} />
        )}

        {activeView === 'folders' && (
          <FolderPicker
            folders={monitoredFolders}
            onAddFolder={handleSelectFolder}
            onRemoveFolder={async (path) => {
              try {
                await api.delete('/monitor/folders', { data: { path } })
                loadFolders()
                loadDocuments()
              } catch (err) {
                console.error('Error removing folder:', err)
              }
            }}
            onSync={handleSync}
            syncing={syncing}
          />
        )}

        {activeView === 'chat' && <ChatWindow />}

        {activeView === 'flashcards' && <Flashcards />}

        {activeView === 'quizzes' && <QuizViewer />}
      </main>
    </div>
  )
}
