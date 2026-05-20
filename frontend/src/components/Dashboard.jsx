export default function Dashboard({ documents, folders, onSelectFolder }) {
  const processed = documents.filter((d) => d.status === 'processed').length
  const pending = documents.filter((d) => d.status === 'pending').length
  const errors = documents.filter((d) => d.status === 'error').length

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="p-6 rounded-lg" style={{ background: 'var(--bg-secondary)' }}>
          <p className="text-3xl font-bold" style={{ color: '#22c55e' }}>{processed}</p>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Procesados</p>
        </div>
        <div className="p-6 rounded-lg" style={{ background: 'var(--bg-secondary)' }}>
          <p className="text-3xl font-bold" style={{ color: '#eab308' }}>{pending}</p>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Pendientes</p>
        </div>
        <div className="p-6 rounded-lg" style={{ background: 'var(--bg-secondary)' }}>
          <p className="text-3xl font-bold" style={{ color: '#ef4444' }}>{errors}</p>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Errores</p>
        </div>
      </div>

      <div className="p-6 rounded-lg mb-6" style={{ background: 'var(--bg-secondary)' }}>
        <h3 className="text-lg font-semibold mb-3">Carpetas monitoreadas</h3>
        {folders.length === 0 ? (
          <p style={{ color: 'var(--text-muted)' }}>No hay carpetas seleccionadas</p>
        ) : (
          <ul className="space-y-2">
            {folders.map((f, i) => (
              <li key={i} style={{ color: 'var(--text-secondary)' }}>{f.path}</li>
            ))}
          </ul>
        )}
        <button
          onClick={onSelectFolder}
          className="mt-4 px-4 py-2 rounded-lg transition-colors text-white"
          style={{ background: 'var(--accent)' }}
        >
          + Agregar carpeta
        </button>
      </div>

      <div className="p-6 rounded-lg" style={{ background: 'var(--bg-secondary)' }}>
        <h3 className="text-lg font-semibold mb-3">Actividad reciente</h3>
        {documents.length === 0 ? (
          <p style={{ color: 'var(--text-muted)' }}>Aun no hay documentos procesados</p>
        ) : (
          <div className="space-y-2">
            {documents.slice(0, 5).map((doc) => (
              <div key={doc.id} className="flex items-center justify-between text-sm">
                <span style={{ color: 'var(--text-secondary)' }}>{doc.filename}</span>
                <span className={`px-2 py-1 rounded text-xs ${
                  doc.status === 'processed' ? 'bg-green-900 text-green-300' :
                  doc.status === 'error' ? 'bg-red-900 text-red-300' :
                  'bg-yellow-900 text-yellow-300'
                }`}>
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
