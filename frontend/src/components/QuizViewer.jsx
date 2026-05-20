import { useState, useEffect } from 'react'
import api from '../api/client'

const PHASES = { CONFIGURE: 0, GENERATING: 1, ANSWER: 2, RESULTS: 3 }

export default function QuizViewer() {
  const [documents, setDocuments] = useState([])
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [numQuestions, setNumQuestions] = useState(5)
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [phase, setPhase] = useState(PHASES.CONFIGURE)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/documents').then((res) => setDocuments(res.data)).catch(() => {})
  }, [])

  async function generateQuiz() {
    if (!selectedDoc) return
    setPhase(PHASES.GENERATING)
    setError('')
    setAnswers({})

    try {
      const res = await api.post(`/content/quizzes/${selectedDoc}`, { num_questions: numQuestions })
      setQuiz(res.data)
      setPhase(PHASES.ANSWER)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error al generar el quiz')
      setPhase(PHASES.CONFIGURE)
    }
  }

  function handleAnswer(questionIdx, answer) {
    setAnswers((prev) => ({ ...prev, [questionIdx]: answer }))
  }

  function calculateScore() {
    if (!quiz?.questions) return 0
    let correct = 0
    quiz.questions.forEach((q, i) => {
      if (answers[i] === q.correct) correct++
    })
    return correct
  }

  function reset() {
    setQuiz(null)
    setAnswers({})
    setPhase(PHASES.CONFIGURE)
    setError('')
  }

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-2xl font-bold mb-6">Quizzes</h2>

      {phase === PHASES.CONFIGURE && (
        <div className="max-w-md space-y-6">
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
              {documents.filter(d => d.status === 'processed').map((doc) => (
                <option key={doc.id} value={doc.id}>{doc.filename}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm mb-2 block" style={{ color: 'var(--text-muted)' }}>Numero de preguntas:</label>
            <input
              type="number"
              min={3}
              max={20}
              value={numQuestions}
              onChange={(e) => setNumQuestions(Math.max(3, Math.min(20, Number(e.target.value))))}
              className="w-full p-3 rounded-lg border focus:outline-none"
              style={{
                background: 'var(--bg-secondary)',
                borderColor: 'var(--border)',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg text-sm text-red-300" style={{ background: '#7f1d1d' }}>
              {error}
            </div>
          )}

          <button
            onClick={generateQuiz}
            disabled={!selectedDoc}
            className="px-6 py-3 rounded-lg text-white transition-colors disabled:opacity-50"
            style={{ background: 'var(--accent)' }}
          >
            Generar Quiz
          </button>
        </div>
      )}

      {phase === PHASES.GENERATING && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="flex justify-center gap-1 mb-4">
              <span className="w-3 h-3 rounded-full animate-bounce" style={{ background: 'var(--accent)' }} />
              <span className="w-3 h-3 rounded-full animate-bounce" style={{ background: 'var(--accent)', animationDelay: '0.1s' }} />
              <span className="w-3 h-3 rounded-full animate-bounce" style={{ background: 'var(--accent)', animationDelay: '0.2s' }} />
            </div>
            <p style={{ color: 'var(--text-muted)' }}>Generando quiz con IA...</p>
          </div>
        </div>
      )}

      {(phase === PHASES.ANSWER || phase === PHASES.RESULTS) && quiz && (
        <div className="flex-1 overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold">{quiz.title}</h3>
            {phase === PHASES.RESULTS && (
              <button
                onClick={reset}
                className="px-4 py-2 rounded-lg text-white transition-colors"
                style={{ background: 'var(--accent)' }}
              >
                Nuevo Quiz
              </button>
            )}
          </div>

          <div className="space-y-6">
            {quiz.questions?.map((q, i) => (
              <div key={i} className="p-4 rounded-lg" style={{ background: 'var(--bg-secondary)' }}>
                <p className="font-medium mb-3">{i + 1}. {q.question}</p>
                <div className="space-y-2">
                  {q.options?.map((opt, j) => {
                    const isCorrect = opt.startsWith(q.correct)
                    const isSelected = answers[i] === opt
                    const showResult = phase === PHASES.RESULTS
                    let bg = 'var(--bg-tertiary)'
                    if (showResult) {
                      if (isCorrect) bg = '#14532d'
                      else if (isSelected) bg = '#7f1d1d'
                    } else if (isSelected) {
                      bg = 'var(--accent)'
                    }
                    return (
                      <label
                        key={j}
                        className="block p-3 rounded-lg cursor-pointer transition-colors"
                        style={{ background: bg, color: showResult && isCorrect ? '#86efac' : showResult && isSelected ? '#fca5a5' : 'var(--text-primary)' }}
                      >
                        <input
                          type={phase === PHASES.RESULTS ? 'button' : 'radio'}
                          name={`q-${i}`}
                          value={opt}
                          checked={isSelected}
                          onChange={() => handleAnswer(i, opt)}
                          disabled={phase === PHASES.RESULTS}
                          className="mr-2"
                        />
                        {opt}
                      </label>
                    )
                  })}
                </div>
                {phase === PHASES.RESULTS && q.explanation && (
                  <p className="mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>{q.explanation}</p>
                )}
              </div>
            ))}
          </div>

          <div className="mt-6">
            {phase === PHASES.ANSWER ? (
              <button
                onClick={() => setPhase(PHASES.RESULTS)}
                className="px-6 py-3 rounded-lg text-white transition-colors"
                style={{ background: 'var(--accent)' }}
              >
                Calificar
              </button>
            ) : (
              <div className="p-4 rounded-lg text-center" style={{ background: 'var(--bg-secondary)' }}>
                <p className="text-2xl font-bold">{calculateScore()} / {quiz.questions?.length || 0}</p>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Calificacion</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
