import { useState, useEffect } from 'react';
import { getClasses } from '../services/api';
import type { Class } from '../types';

function Classes() {
  const [classes, setClasses] = useState<Class[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadClasses();
  }, []);

  const loadClasses = async () => {
    try {
      setLoading(true);
      const response = await getClasses();
      setClasses(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar las clases');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="text-gray-600">Cargando clases...</div>
    </div>
  );

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-8">Gestión de Clases</h2>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID XML</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Curso</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Límite</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Instructores</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {classes.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No hay clases registradas. Importa un archivo XML para cargar las clases.
                  </td>
                </tr>
              ) : (
                classes.map(classItem => (
                  <tr key={classItem.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{classItem.xml_id}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{classItem.offering_name || 'Sin curso'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{classItem.class_limit}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {classItem.instructor_names && classItem.instructor_names.length > 0 
                        ? classItem.instructor_names.join(', ') 
                        : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded ${classItem.committed ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {classItem.committed ? 'Comprometida' : 'Pendiente'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Classes;
