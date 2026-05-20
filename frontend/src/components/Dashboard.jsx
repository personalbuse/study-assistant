export default function Dashboard({ documents, folders, onSelectFolder }) {
  const processed = documents.filter((d) => d.status === 'processed').length
  const pending = documents.filter((d) => d.status === 'pending').length
  const errors = documents.filter((d) => d.status === 'error').length

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-gray-800 p-6 rounded-lg">
          <p className="text-3xl font-bold text-green-400">{processed}</p>
          <p className="text-gray-400">Procesados</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg">
          <p className="text-3xl font-bold text-yellow-400">{pending}</p>
          <p className="text-gray-400">Pendientes</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg">
          <p className="text-3xl font-bold text-red-400">{errors}</p>
          <p className="text-gray-400">Errores</p>
        </div>
      </div>

      <div className="bg-gray-800 p-6 rounded-lg mb-6">
        <h3 className="text-lg font-semibold mb-3">Carpetas monitoreadas</h3>
        {folders.length === 0 ? (
          <p className="text-gray-400">No hay carpetas seleccionadas</p>
        ) : (
          <ul className="space-y-2">
            {folders.map((f, i) => (
              <li key={i} className="text-gray-300">📁 {f.path}</li>
            ))}
          </ul>
        )}
        <button
          onClick={onSelectFolder}
          className="mt-4 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
        >
          + Agregar carpeta
        </button>
      </div>

      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-lg font-semibold mb-3">Actividad reciente</h3>
        {documents.length === 0 ? (
          <p className="text-gray-400">Aún no hay documentos procesados</p>
        ) : (
          <div className="space-y-2">
            {documents.slice(0, 5).map((doc) => (
              <div key={doc.id} className="flex items-center justify-between text-sm">
                <span className="text-gray-300">{doc.filename}</span>
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
