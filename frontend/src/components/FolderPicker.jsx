export default function FolderPicker({ folders, onAddFolder, onRemoveFolder, onSync, syncing }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Carpetas Monitoreadas</h2>
        {folders.length > 0 && (
          <button
            onClick={onSync}
            disabled={syncing}
            className="px-6 py-3 rounded-lg transition-colors disabled:opacity-50 text-white"
            style={{ background: syncing ? 'var(--text-muted)' : '#16a34a' }}
          >
            {syncing ? 'Sincronizando...' : 'Sincronizar fuentes'}
          </button>
        )}
      </div>

      <button
        onClick={onAddFolder}
        className="mb-6 px-6 py-3 rounded-lg transition-colors"
        style={{ background: 'var(--accent)', color: 'var(--accent-text)' }}
      >
        Seleccionar carpeta
      </button>

      {folders.length === 0 ? (
        <div className="text-center mt-12" style={{ color: 'var(--text-muted)' }}>
          <p>No hay carpetas seleccionadas</p>
          <p className="text-sm mt-2">Haz clic en Seleccionar carpeta para empezar</p>
          <p className="text-sm mt-1">Luego presiona Sincronizar fuentes para indexar tus documentos</p>
        </div>
      ) : (
        <div className="space-y-3">
          {folders.map((folder, i) => (
            <div
              key={i}
              className="p-4 rounded-lg flex items-center justify-between"
              style={{ background: 'var(--bg-secondary)' }}
            >
              <span style={{ color: 'var(--text-secondary)' }}>{folder.path}</span>
              <button
                onClick={() => onRemoveFolder(folder.path)}
                className="px-3 py-1 rounded text-sm text-white transition-colors"
                style={{ background: '#dc2626' }}
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
