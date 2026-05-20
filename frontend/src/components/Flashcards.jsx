import { useState, useEffect } from 'react'
import api from '../api/client'

export default function Flashcards() {
  const [documents, setDocuments] = useState([])
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [flashcards, setFlashcards] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.get('/documents').then((res) => setDocuments(res.data)).catch(() => {})
  }, [])

  async function loadFlashcards(docId) {
    setSelectedDoc(docId)
    setFlipped(false)
    setCurrentIndex(0)
    setLoading(true)

    try {
      let res = await api.get(`/content/flashcards/${docId}`)
      if (!res.data || res.data.length === 0) {
        res = await api.post(`/content/flashcards/${docId}`)
      }
      setFlashcards(res.data || [])
    } catch (err) {
      console.error('Error loading flashcards:', err)
    } finally {
      setLoading(false)
    }
  }

  const current = flashcards[currentIndex]

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-2xl font-bold mb-6">Flashcards</h2>

      <div className="mb-6">
        <label className="text-sm mb-2 block" style={{ color: 'var(--text-muted)' }}>Selecciona un documento:</label>
        <select
          onChange={(e) => e.target.value && loadFlashcards(Number(e.target.value))}
          className="w-full p-3 rounded-lg border focus:outline-none"
          style={{
            background: 'var(--bg-secondary)',
            borderColor: 'var(--border)',
            color: 'var(--text-primary)',
          }}
        >
          <option value="">-- Seleccionar --</option>
          {documents.map((doc) => (
            <option key={doc.id} value={doc.id}>{doc.filename}</option>
          ))}
        </select>
      </div>

      {loading && <div className="text-center" style={{ color: 'var(--text-muted)' }}>Generando flashcards...</div>}

      {current && !loading && (
        <div className="flex-1 flex flex-col items-center justify-center">
          <div
            onClick={() => setFlipped(!flipped)}
            className="w-full max-w-lg h-64 rounded-xl p-8 cursor-pointer flex items-center justify-center text-center transition-all"
            style={{ background: 'var(--bg-secondary)' }}
          >
            <div>
              <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>
                {flipped ? 'Respuesta' : 'Pregunta'} · {currentIndex + 1}/{flashcards.length}
              </p>
              <p className="text-xl">{flipped ? current.answer : current.question}</p>
              {current.topic && (
                <p className="text-sm mt-4" style={{ color: 'var(--accent)' }}>#{current.topic}</p>
              )}
            </div>
          </div>
          <p className="text-sm mt-4" style={{ color: 'var(--text-muted)' }}>Haz clic para voltear</p>

          <div className="flex gap-4 mt-6">
            <button
              onClick={() => { setFlipped(false); setCurrentIndex(Math.max(0, currentIndex - 1)) }}
              disabled={currentIndex === 0}
              className="px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
              style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
            >
              Anterior
            </button>
            <button
              onClick={() => { setFlipped(false); setCurrentIndex(Math.min(flashcards.length - 1, currentIndex + 1)) }}
              disabled={currentIndex === flashcards.length - 1}
              className="px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
              style={{ background: 'var(--accent)', color: 'var(--accent-text)' }}
            >
              Siguiente
            </button>
          </div>
        </div>
      )}

      {!current && !loading && selectedDoc && (
        <div className="text-center" style={{ color: 'var(--text-muted)' }}>No hay flashcards para este documento</div>
      )}
    </div>
  )
}
