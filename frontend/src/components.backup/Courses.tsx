import { useState, useEffect } from 'react';
import { getCourses } from '../services/api';
import type { Course } from '../types';

function Courses() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    try {
      setLoading(true);
      const response = await getCourses();
      setCourses(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar los cursos');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Cargando cursos...</div>;

  return (
    <div>
      <h2 style={{ marginBottom: '2rem' }}>📚 Gestión de Cursos</h2>

      {error && <div className="error">{error}</div>}

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID XML</th>
                <th>Código</th>
                <th>Nombre</th>
                <th>Clases</th>
              </tr>
            </thead>
            <tbody>
              {courses.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: '2rem' }}>
                    No hay cursos registrados. Importa un archivo XML para cargar los cursos.
                  </td>
                </tr>
              ) : (
                courses.map(course => (
                  <tr key={course.id}>
                    <td>{course.xml_id}</td>
                    <td><strong>{course.code}</strong></td>
                    <td>{course.name}</td>
                    <td>
                      <span className="badge badge-primary">{course.class_count || 0}</span>
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

export default Courses;
