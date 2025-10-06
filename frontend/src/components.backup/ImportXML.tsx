import { useState } from 'react';
import { importXML } from '../services/api';
import type { ImportStats } from '../types';

function ImportXML() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [importStats, setImportStats] = useState<any>(null);
  const [clearExisting, setClearExisting] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setSuccess(null);
      setError(null);
      setImportStats(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('Por favor selecciona un archivo XML');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const formData = new FormData();
      formData.append('file', file);
      if (clearExisting) {
        formData.append('clear_existing', 'true');
      }

      const response = await importXML(formData);
      
      if (response.data.success) {
        setSuccess(response.data.message);
        setImportStats(response.data.stats);
        setFile(null);
        // Reset file input
        const fileInput = document.getElementById('file-input') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
      } else {
        setError('Error al importar el archivo');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al importar el archivo XML');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: '2rem' }}>📤 Importar Datos desde XML</h2>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Cargar Archivo XML</h3>
        </div>

        {success && (
          <div className="success">
            ✅ {success}
          </div>
        )}

        {error && (
          <div className="error">
            ❌ {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="file-input" className="form-label">
              Seleccionar archivo XML (UniTime format)
            </label>
            <input
              id="file-input"
              type="file"
              accept=".xml"
              onChange={handleFileChange}
              className="form-control"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={clearExisting}
                onChange={(e) => setClearExisting(e.target.checked)}
                disabled={loading}
                style={{ marginRight: '0.5rem' }}
              />
              Limpiar datos existentes antes de importar
            </label>
          </div>

          {file && (
            <div style={{ marginBottom: '1rem', padding: '0.5rem', background: '#f0f0f0', borderRadius: '4px' }}>
              📄 Archivo seleccionado: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(2)} KB)
            </div>
          )}

          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={loading || !file}
          >
            {loading ? 'Importando...' : 'Importar XML'}
          </button>
        </form>

        {importStats && (
          <div style={{ marginTop: '2rem' }}>
            <h4 style={{ marginBottom: '1rem' }}>📊 Resultados de la Importación</h4>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Aulas</div>
                <div className="stat-value">{importStats.rooms}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Instructores</div>
                <div className="stat-value">{importStats.instructors}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Cursos</div>
                <div className="stat-value">{importStats.courses}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Clases</div>
                <div className="stat-value">{importStats.classes}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Slots de Tiempo</div>
                <div className="stat-value">{importStats.time_slots}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Estudiantes</div>
                <div className="stat-value">{importStats.students}</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">ℹ️ Información</h3>
        </div>
        <div>
          <p style={{ marginBottom: '1rem' }}>
            <strong>Formato esperado:</strong> Archivo XML en formato UniTime Course Timetabling.
          </p>
          <p style={{ marginBottom: '1rem' }}>
            El sistema importará la siguiente información:
          </p>
          <ul style={{ marginLeft: '1.5rem', marginBottom: '1rem' }}>
            <li>🏫 Aulas (rooms) con su capacidad y ubicación</li>
            <li>👨‍🏫 Instructores (instructors)</li>
            <li>📚 Cursos (offerings)</li>
            <li>📝 Clases (classes) con sus configuraciones</li>
            <li>⏰ Slots de tiempo disponibles</li>
            <li>👨‍🎓 Estudiantes y sus inscripciones</li>
          </ul>
          <p style={{ color: '#e74c3c' }}>
            <strong>⚠️ Advertencia:</strong> Si marcas "Limpiar datos existentes", 
            se eliminarán todos los datos actuales antes de importar.
          </p>
        </div>
      </div>
    </div>
  );
}

export default ImportXML;
