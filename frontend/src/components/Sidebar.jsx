const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'documents', label: 'Documentos', icon: '📄' },
  { id: 'folders', label: 'Carpetas', icon: '📁' },
  { id: 'chat', label: 'Chat IA', icon: '💬' },
  { id: 'flashcards', label: 'Flashcards', icon: '🃏' },
  { id: 'quizzes', label: 'Quizzes', icon: '📝' },
]

export default function Sidebar({ activeView, onNavigate, folderCount, documentCount }) {
  return (
    <aside className="w-64 bg-gray-800 p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-blue-400">Study Assistant</h1>
        <p className="text-sm text-gray-400">IA + RAG</p>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              activeView === item.id
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-700'
            }`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="border-t border-gray-700 pt-4 mt-4 space-y-2 text-sm text-gray-400">
        <p>📂 {folderCount} carpetas</p>
        <p>📄 {documentCount} documentos</p>
      </div>
    </aside>
  )
}
