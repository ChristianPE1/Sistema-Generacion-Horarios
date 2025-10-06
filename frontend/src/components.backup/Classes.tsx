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

  if (loading) return <div className="loading">Cargando clases...</div>;

  return (
    <div>
      <h2 style={{ marginBottom: '2rem' }}>📝 Gestión de Clases</h2>

      {error && <div className="error">{error}</div>}

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID XML</th>
                <th>Curso</th>
                <th>Límite</th>
                <th>Instructores</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {classes.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem' }}>
                    No hay clases registradas. Importa un archivo XML para cargar las clases.
                  </td>
                </tr>
              ) : (
                classes.map(classItem => (
                  <tr key={classItem.id}>
                    <td>{classItem.xml_id}</td>
                    <td>{classItem.offering_name || 'Sin curso'}</td>
                    <td>{classItem.class_limit}</td>
                    <td>
                      {classItem.instructor_names && classItem.instructor_names.length > 0 
                        ? classItem.instructor_names.join(', ') 
                        : '-'}
                    </td>
                    <td>
                      <span className={`badge ${classItem.committed ? 'badge-success' : 'badge-secondary'}`}>
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
