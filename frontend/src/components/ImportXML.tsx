import { useState } from 'react';
import { importXML } from '../services/api';

interface ImportStats {
  rooms: number;
  instructors: number;
  courses: number;
  classes: number;
  students: number;
  timeslots: number;
}

function ImportXML() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [stats, setStats] = useState<ImportStats | null>(null);
  const [clearExisting, setClearExisting] = useState(true);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setSuccess(false);
      setStats(null);
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
      setSuccess(false);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('clear_existing', clearExisting ? 'true' : 'false');

      const response = await importXML(formData);
      
      setStats(response.data.stats);
      setSuccess(true);
      setFile(null);
      
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al importar el archivo XML');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-8">Importar Datos XML</h2>

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Archivo XML (formato UniTime)
            </label>
            <input
              type="file"
              accept=".xml"
              onChange={handleFileChange}
              disabled={loading}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="clearExisting"
              checked={clearExisting}
              onChange={(e) => setClearExisting(e.target.checked)}
              disabled={loading}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="clearExisting" className="ml-2 block text-sm text-gray-700">
              Limpiar datos existentes antes de importar
            </label>
          </div>

          <button
            type="submit"
            disabled={loading || !file}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium"
          >
            {loading ? 'Importando...' : 'Importar XML'}
          </button>
        </form>

        {error && (
          <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {success && stats && (
          <div className="mt-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            <p className="font-medium mb-2">Importación exitosa!</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.rooms}</div>
                <div className="text-sm">Aulas</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.instructors}</div>
                <div className="text-sm">Instructores</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.courses}</div>
                <div className="text-sm">Cursos</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.classes}</div>
                <div className="text-sm">Clases</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.students}</div>
                <div className="text-sm">Estudiantes</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.timeslots}</div>
                <div className="text-sm">Slots de Tiempo</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-bold text-blue-900 mb-3">Información</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li>• El archivo debe estar en formato XML de UniTime Course Timetabling</li>
          <li>• La importación puede tardar varios segundos para archivos grandes</li>
          <li>• Si seleccionas "Limpiar datos existentes", se eliminarán todos los datos actuales</li>
          <li>• Los IDs XML deben ser únicos para cada entidad</li>
        </ul>
      </div>
    </div>
  );
}

export default ImportXML;
