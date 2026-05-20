import { useState } from 'react'
import api from '../api/client'

export default function ChatWindow() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  async function sendMessage() {
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await api.post('/chat/ask', { message: input })
      const botMessage = {
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources,
      }
      setMessages((prev) => [...prev, botMessage])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error al obtener respuesta', sources: [] },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-2xl font-bold mb-4">Chat de Estudio IA</h2>

      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-center mt-12" style={{ color: 'var(--text-muted)' }}>
            <p>Pregunta sobre tus documentos academicos</p>
            <p className="text-sm mt-2">Ej: Que es subnetting?, Explica TCP/IP</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className="p-4 rounded-lg"
            style={{
              background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg-secondary)',
              color: msg.role === 'user' ? 'var(--accent-text)' : 'var(--text-primary)',
              marginLeft: msg.role === 'user' ? '3rem' : '0',
              marginRight: msg.role === 'assistant' ? '3rem' : '0',
            }}
          >
            <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
            {msg.sources && msg.sources.length > 0 && (
              <div className="mt-3 text-xs pt-2" style={{
                color: 'var(--text-muted)',
                borderTop: '1px solid var(--border)',
              }}>
                <strong>Fuentes: </strong>
                {msg.sources.map((s, j) => (
                  <span key={j} className="ml-1">
                    {s.filename} (pag {s.page})
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="p-4 rounded-lg" style={{ background: 'var(--bg-secondary)', marginRight: '3rem' }}>
            <div className="flex gap-1">
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--text-muted)' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--text-muted)', animationDelay: '0.1s' }} />
              <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--text-muted)', animationDelay: '0.2s' }} />
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Pregunta sobre tus documentos..."
          className="flex-1 p-3 rounded-lg border focus:outline-none"
          style={{
            background: 'var(--bg-secondary)',
            borderColor: 'var(--border)',
            color: 'var(--text-primary)',
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          className="px-6 py-3 rounded-lg transition-colors disabled:opacity-50"
          style={{ background: 'var(--accent)', color: 'var(--accent-text)' }}
        >
          Enviar
        </button>
      </div>
    </div>
  )
}
