export default function DocumentList({ documents, onReload }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Documentos</h2>
        <button
          onClick={onReload}
          className="px-4 py-2 rounded-lg transition-colors"
          style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
        >
          Recargar
        </button>
      </div>

      {documents.length === 0 ? (
        <div className="text-center mt-12" style={{ color: 'var(--text-muted)' }}>
          <p>No hay documentos procesados aun</p>
          <p className="text-sm mt-2">Agrega carpetas para comenzar a monitorear</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="p-4 rounded-lg flex items-center justify-between"
              style={{ background: 'var(--bg-secondary)' }}
            >
              <div>
                <p className="font-semibold">{doc.filename}</p>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {doc.file_type?.toUpperCase()} · {doc.page_count} paginas
                </p>
              </div>
              <span className={`px-3 py-1 rounded text-sm ${
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
  )
}
