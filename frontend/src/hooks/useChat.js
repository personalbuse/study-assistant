import { useState } from 'react'
import api from '../api/client'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  async function sendMessage(text) {
    const userMsg = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await api.post('/chat/ask', { message: text })
      const botMsg = {
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources,
      }
      setMessages(prev => [...prev, botMsg])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Error al obtener respuesta', sources: [] },
      ])
    } finally {
      setLoading(false)
    }
  }

  return { messages, loading, sendMessage }
}
