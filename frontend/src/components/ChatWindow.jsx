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
          <div className="text-center text-gray-400 mt-12">
            <p className="text-4xl mb-4">💬</p>
            <p>Pregunta sobre tus documentos académicos</p>
            <p className="text-sm mt-2">Ej: "¿Qué es subnetting?", "Explica TCP/IP"</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-4 rounded-lg ${
              msg.role === 'user'
                ? 'bg-blue-600 ml-12'
                : 'bg-gray-700 mr-12'
            }`}
          >
            <p className="whitespace-pre-wrap">{msg.content}</p>
            {msg.sources && msg.sources.length > 0 && (
              <div className="mt-3 text-xs text-gray-400 border-t border-gray-600 pt-2">
                <strong>Fuentes:</strong>
                {msg.sources.map((s, j) => (
                  <span key={j} className="ml-2">
                    {s.filename} (pág {s.page}, relevancia: {s.relevance})
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="bg-gray-700 p-4 rounded-lg mr-12 animate-pulse">
            Pensando...
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
          className="flex-1 p-3 rounded-lg bg-gray-800 border border-gray-600 focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          className="px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          Enviar
        </button>
      </div>
    </div>
  )
}
