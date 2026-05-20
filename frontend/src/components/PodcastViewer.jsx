import { useState, useEffect } from 'react'
import api from '../api/client'

export default function PodcastViewer() {
  const [documents, setDocuments] = useState([])
  const [folders, setFolders] = useState([])
  const [podcasts, setPodcasts] = useState([])
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [selectedFolder, setSelectedFolder] = useState(null)
  const [tab, setTab] = useState('document')
  const [loading, setLoading] = useState(false)
  const [statusMsg, setStatusMsg] = useState('')
  const [error, setError] = useState('')
  const [playingId, setPlayingId] = useState(null)

  useEffect(() => {
    api.get('/documents').then((res) => setDocuments(res.data)).catch(() => {})
    api.get('/monitor/folders').then((res) => setFolders(res.data.folders || [])).catch(() => {})
    loadPodcasts()
  }, [])

  async function loadPodcasts() {
    try {
      const res = await api.get('/podcasts')
      setPodcasts(res.data)
    } catch {
      console.error('Error loading podcasts')
    }
  }

  async function generatePodcast() {
    setLoading(true)
    setError('')
    setPlayingId(null)

    try {
      let endpoint
      if (tab === 'document') {
        if (!selectedDoc) return
        endpoint = `/podcasts/by-document/${selectedDoc}`
        setStatusMsg('Generando guion con IA...')
      } else {
        if (!selectedFolder) return
        endpoint = `/podcasts/by-folder/${selectedFolder}`
        setStatusMsg('Generando guion con IA...')
      }

      await api.post(endpoint)

      setStatusMsg('Sintetizando audio...')
      await new Promise((r) => setTimeout(r, 500))

      await loadPodcasts()
      setStatusMsg('')
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error al generar podcast')
    } finally {
      setLoading(false)
      setStatusMsg('')
    }
  }

  async function deletePodcast(id) {
    try {
      await api.delete(`/podcasts/${id}`)
      if (playingId === id) setPlayingId(null)
      loadPodcasts()
    } catch (err) {
      console.error('Error deleting podcast:', err)
    }
  }

  function formatDuration(seconds) {
    if (seconds < 1) return ''
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')} min`
  }

  function formatDate(iso) {
    return new Date(iso).toLocaleDateString('es-CO', {
      day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
    })
  }

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-2xl font-bold mb-6">Podcasts</h2>

      {!loading && (
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => { setTab('document'); setSelectedFolder(null) }}
            className="px-4 py-2 rounded-lg transition-colors"
            style={{
              background: tab === 'document' ? 'var(--accent)' : 'var(--bg-tertiary)',
              color: tab === 'document' ? 'var(--accent-text)' : 'var(--text-secondary)',
            }}
          >
            Por documento
          </button>
          <button
            onClick={() => { setTab('folder'); setSelectedDoc(null) }}
            className="px-4 py-2 rounded-lg transition-colors"
            style={{
              background: tab === 'folder' ? 'var(--accent)' : 'var(--bg-tertiary)',
              color: tab === 'folder' ? 'var(--accent-text)' : 'var(--text-secondary)',
            }}
          >
            Por carpeta
          </button>
        </div>
      )}

      {tab === 'document' && !loading && (
        <div className="max-w-md space-y-4 mb-6">
          <div>
            <label className="text-sm mb-2 block" style={{ color: 'var(--text-muted)' }}>Documento:</label>
            <select
              value={selectedDoc || ''}
              onChange={(e) => setSelectedDoc(e.target.value ? Number(e.target.value) : null)}
              className="w-full p-3 rounded-lg border focus:outline-none"
              style={{
                background: 'var(--bg-secondary)',
                borderColor: 'var(--border)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="">-- Seleccionar --</option>
              {documents.filter((d) => d.status === 'processed').map((doc) => (
                <option key={doc.id} value={doc.id}>{doc.filename}</option>
              ))}
            </select>
          </div>
          <button
            onClick={generatePodcast}
            disabled={!selectedDoc}
            className="px-6 py-3 rounded-lg transition-colors disabled:opacity-50"
            style={{ background: 'var(--accent)', color: 'var(--accent-text)' }}
          >
            Generar Podcast
          </button>
        </div>
      )}

      {tab === 'folder' && !loading && (
        <div className="max-w-md space-y-4 mb-6">
          <div>
            <label className="text-sm mb-2 block" style={{ color: 'var(--text-muted)' }}>Carpeta:</label>
            <select
              value={selectedFolder || ''}
              onChange={(e) => setSelectedFolder(e.target.value ? Number(e.target.value) : null)}
              className="w-full p-3 rounded-lg border focus:outline-none"
              style={{
                background: 'var(--bg-secondary)',
                borderColor: 'var(--border)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="">-- Seleccionar --</option>
              {folders.map((f) => (
                <option key={f.id} value={f.id}>{f.path}</option>
              ))}
            </select>
          </div>
          <button
            onClick={generatePodcast}
            disabled={!selectedFolder}
            className="px-6 py-3 rounded-lg transition-colors disabled:opacity-50"
            style={{ background: 'var(--accent)', color: 'var(--accent-text)' }}
          >
            Generar Podcast
          </button>
        </div>
      )}

      {loading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="flex justify-center gap-1 mb-4">
              <span className="w-3 h-3 rounded-full animate-bounce" style={{ background: 'var(--accent)' }} />
              <span className="w-3 h-3 rounded-full animate-bounce" style={{ background: 'var(--accent)', animationDelay: '0.1s' }} />
              <span className="w-3 h-3 rounded-full animate-bounce" style={{ background: 'var(--accent)', animationDelay: '0.2s' }} />
            </div>
            <p style={{ color: 'var(--text-muted)' }}>{statusMsg || 'Generando podcast...'}</p>
          </div>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg mb-4 text-sm" style={{ background: '#3b1010', color: '#fca5a5' }}>
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {podcasts.length === 0 && !loading && (
          <div className="text-center mt-12" style={{ color: 'var(--text-muted)' }}>
            <p>No hay podcasts generados aun</p>
            <p className="text-sm mt-2">Selecciona un documento o carpeta y genera tu primer podcast</p>
          </div>
        )}

        <div className="space-y-3">
          {podcasts.map((p) => (
            <div
              key={p.id}
              className="p-4 rounded-lg"
              style={{ background: 'var(--bg-secondary)' }}
            >
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-semibold">{p.title}</p>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    {p.source_count} fuente{p.source_count !== 1 ? 's' : ''}
                    {p.duration_seconds ? ` · ${formatDuration(p.duration_seconds)}` : ''}
                    {' · '}
                    {formatDate(p.created_at)}
                  </p>
                </div>
                <div className="flex gap-2">
                  {p.has_audio && (
                    <button
                      onClick={() => setPlayingId(playingId === p.id ? null : p.id)}
                      className="px-3 py-1 rounded text-sm transition-colors"
                      style={{
                        background: playingId === p.id ? 'var(--accent)' : 'var(--bg-tertiary)',
                        color: playingId === p.id ? 'var(--accent-text)' : 'var(--text-secondary)',
                      }}
                    >
                      {playingId === p.id ? 'Cerrar' : 'Reproducir'}
                    </button>
                  )}
                  <button
                    onClick={() => deletePodcast(p.id)}
                    className="px-3 py-1 rounded text-sm text-white transition-colors"
                    style={{ background: '#dc2626' }}
                  >
                    Eliminar
                  </button>
                </div>
              </div>
              {playingId === p.id && p.has_audio && (
                <div className="mt-3 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
                  <audio controls autoPlay className="w-full" style={{ height: 40 }}>
                    <source src={`/api/podcasts/${p.id}/audio`} type="audio/mpeg" />
                  </audio>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
