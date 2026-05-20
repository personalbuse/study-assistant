import { useState, useEffect } from 'react'
import api from '../api/client'

export default function QuizViewer() {
  const [documents, setDocuments] = useState([])
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [showResults, setShowResults] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.get('/documents').then((res) => setDocuments(res.data)).catch(() => {})
  }, [])

  async function loadQuiz(docId) {
    setSelectedDoc(docId)
    setAnswers({})
    setShowResults(false)
    setLoading(true)

    try {
      let res = await api.get(`/content/quizzes/${docId}`)
      if (!res.data || !res.data.questions || res.data.questions.length === 0) {
        res = await api.post(`/content/quizzes/${docId}`)
      }
      setQuiz(res.data)
    } catch (err) {
      console.error('Error loading quiz:', err)
    } finally {
      setLoading(false)
    }
  }

  function handleAnswer(questionIdx, answer) {
    setAnswers((prev) => ({ ...prev, [questionIdx]: answer }))
  }

  function calculateScore() {
    if (!quiz) return 0
    let correct = 0
    quiz.questions.forEach((q, i) => {
      if (answers[i] === q.correct) correct++
    })
    return correct
  }

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-2xl font-bold mb-6">Quizzes</h2>

      <div className="mb-6">
        <label className="text-sm text-gray-400 mb-2 block">Selecciona un documento:</label>
        <select
          onChange={(e) => e.target.value && loadQuiz(Number(e.target.value))}
          className="w-full p-3 rounded-lg bg-gray-800 border border-gray-600"
        >
          <option value="">-- Seleccionar --</option>
          {documents.map((doc) => (
            <option key={doc.id} value={doc.id}>{doc.filename}</option>
          ))}
        </select>
      </div>

      {loading && <div className="text-center text-gray-400">Generando quiz...</div>}

      {quiz && !loading && (
        <div className="flex-1 overflow-y-auto">
          <h3 className="text-xl font-semibold mb-4">{quiz.title}</h3>

          <div className="space-y-6">
            {quiz.questions?.map((q, i) => (
              <div key={i} className="bg-gray-800 p-4 rounded-lg">
                <p className="font-medium mb-3">{i + 1}. {q.question}</p>
                <div className="space-y-2">
                  {q.options?.map((opt, j) => (
                    <label
                      key={j}
                      className={`block p-3 rounded-lg cursor-pointer transition-colors ${
                        showResults
                          ? opt.startsWith(q.correct)
                            ? 'bg-green-900 border border-green-500'
                            : answers[i] === opt
                            ? 'bg-red-900 border border-red-500'
                            : 'bg-gray-700'
                          : answers[i] === opt
                          ? 'bg-blue-600'
                          : 'bg-gray-700 hover:bg-gray-600'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`q-${i}`}
                        value={opt}
                        checked={answers[i] === opt}
                        onChange={() => handleAnswer(i, opt)}
                        disabled={showResults}
                        className="mr-2"
                      />
                      {opt}
                    </label>
                  ))}
                </div>
                {showResults && q.explanation && (
                  <p className="mt-2 text-sm text-gray-400">{q.explanation}</p>
                )}
              </div>
            ))}
          </div>

          {!showResults ? (
            <button
              onClick={() => setShowResults(true)}
              className="mt-6 px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Calificar
            </button>
          ) : (
            <div className="mt-6 p-4 bg-gray-800 rounded-lg text-center">
              <p className="text-2xl font-bold">
                {calculateScore()} / {quiz.questions?.length || 0}
              </p>
              <p className="text-gray-400">Calificación</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
