export default function FolderPicker({ folders, onAddFolder, onRemoveFolder, onSync, syncing }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Carpetas Monitoreadas</h2>
        {folders.length > 0 && (
          <button
            onClick={onSync}
            disabled={syncing}
            className="px-6 py-3 bg-green-600 rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {syncing ? (
              <>
                <span className="animate-spin">⏳</span>
                Sincronizando...
              </>
            ) : (
              <>
                🔄 Sincronizar fuentes
              </>
            )}
          </button>
        )}
      </div>

      <button
        onClick={onAddFolder}
        className="mb-6 px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
      >
        📁 Seleccionar carpeta
      </button>

      {folders.length === 0 ? (
        <div className="text-center text-gray-400 mt-12">
          <p className="text-4xl mb-4">📂</p>
          <p>No hay carpetas seleccionadas</p>
          <p className="text-sm mt-2">Haz clic en "Seleccionar carpeta" para empezar</p>
          <p className="text-sm mt-1">Luego presiona "Sincronizar fuentes" para indexar tus documentos</p>
        </div>
      ) : (
        <div className="space-y-3">
          {folders.map((folder, i) => (
            <div
              key={i}
              className="bg-gray-800 p-4 rounded-lg flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <span>📁</span>
                <span className="text-gray-300">{folder.path}</span>
              </div>
              <button
                onClick={() => onRemoveFolder(folder.path)}
                className="px-3 py-1 bg-red-700 rounded hover:bg-red-600 transition-colors text-sm"
              >
                Eliminar
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
