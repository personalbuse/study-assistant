const navItems = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'documents', label: 'Documentos' },
  { id: 'folders', label: 'Carpetas' },
  { id: 'chat', label: 'Chat IA' },
  { id: 'flashcards', label: 'Flashcards' },
  { id: 'quizzes', label: 'Quizzes' },
]

export default function Sidebar({ activeView, onNavigate, folderCount, documentCount, theme, onToggleTheme }) {
  return (
    <aside className="w-64 p-4 flex flex-col border-r" style={{
      backgroundColor: 'var(--bg-secondary)',
      borderColor: 'var(--border)',
    }}>
      <div className="mb-8">
        <h1 className="text-xl font-bold" style={{ color: 'var(--accent)' }}>Study Assistant</h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>IA + RAG</p>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors"
            style={{
              background: activeView === item.id ? 'var(--accent)' : 'transparent',
              color: activeView === item.id ? '#fff' : 'var(--text-secondary)',
            }}
            onMouseEnter={(e) => {
              if (activeView !== item.id) e.target.style.background = 'var(--bg-tertiary)'
            }}
            onMouseLeave={(e) => {
              if (activeView !== item.id) e.target.style.background = 'transparent'
            }}
          >
            <span style={{ width: 20, height: 20 }}>
              <svg viewBox="0 0 20 20" fill="currentColor" width={20} height={20}>
                {item.id === 'dashboard' && <path d="M3 3h6v8H3V3zm0 10h6v4H3v-4zm8-10h6v4h-6V3zm0 6h6v8h-6V9z"/>}
                {item.id === 'documents' && <path d="M4 2a2 2 0 00-2 2v12a2 2 0 002 2h8l6-6V4a2 2 0 00-2-2H4zm0 2h10v2H4V4zm0 4h10v2H4V8zm0 4h6v2H4v-2z"/>}
                {item.id === 'folders' && <path d="M2 4a2 2 0 012-2h4l2 2h6a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V4z"/>}
                {item.id === 'chat' && <path d="M2 3a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H6l-4 4V3z"/>}
                {item.id === 'flashcards' && <path d="M4 2a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V4a2 2 0 00-2-2H4zm0 2h12v4H4V4zm0 6h12v4H4v-4z"/>}
                {item.id === 'quizzes' && <path d="M9 2a7 7 0 105.3 11.7l3.5 3.5a1 1 0 001.4-1.4l-3.5-3.5A7 7 0 009 2zm0 2a5 5 0 110 10A5 5 0 019 4zm-1 2v2H6v2h2v2h2v-2h2V8h-2V6H8z"/>}
              </svg>
            </span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="pt-4 mt-4 space-y-2 text-sm" style={{
        borderTop: '1px solid var(--border)',
        color: 'var(--text-muted)',
      }}>
        <p>{folderCount} carpetas</p>
        <p>{documentCount} documentos</p>
        <button
          onClick={onToggleTheme}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors"
          style={{ color: 'var(--text-secondary)' }}
          onMouseEnter={(e) => e.target.style.background = 'var(--bg-tertiary)'}
          onMouseLeave={(e) => e.target.style.background = 'transparent'}
        >
          <svg viewBox="0 0 20 20" fill="currentColor" width={16} height={16}>
            {theme === 'dark' ? (
              <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
            ) : (
              <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
            )}
          </svg>
          <span>{theme === 'dark' ? 'Claro' : 'Oscuro'}</span>
        </button>
      </div>
    </aside>
  )
}
