import { useState, useEffect } from 'react';
import { getDashboardStats } from '../services/api';
import type { DashboardStats } from '../types';

function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const response = await getDashboardStats();
      setStats(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar las estadísticas');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Cargando estadísticas...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!stats) return null;

  return (
    <div>
      <h2 style={{ marginBottom: '2rem' }}>📊 Dashboard del Sistema</h2>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Aulas</div>
          <div className="stat-value">{stats.rooms.total}</div>
          <div className="stat-sublabel">
            Capacidad promedio: {stats.rooms.avg_capacity.toFixed(0)}
            <br />
            Con restricciones: {stats.rooms.with_constraints}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Instructores</div>
          <div className="stat-value">{stats.instructors.total}</div>
          <div className="stat-sublabel">
            Con clases asignadas: {stats.instructors.with_classes}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Cursos</div>
          <div className="stat-value">{stats.courses.total}</div>
          <div className="stat-sublabel">
            Con clases: {stats.courses.with_classes}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Clases</div>
          <div className="stat-value">{stats.classes.total}</div>
          <div className="stat-sublabel">
            Comprometidas: {stats.classes.committed}
            <br />
            Con instructor: {stats.classes.with_instructor}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Estudiantes</div>
          <div className="stat-value">{stats.students.total}</div>
          <div className="stat-sublabel">
            Inscritos: {stats.students.enrolled}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Slots de Tiempo</div>
          <div className="stat-value">{stats.timeslots.total}</div>
          <div className="stat-sublabel">
            Horarios disponibles
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Resumen del Sistema</h3>
        </div>
        <div>
          <p style={{ marginBottom: '1rem' }}>
            El sistema cuenta con <strong>{stats.classes.total} clases</strong> distribuidas 
            en <strong>{stats.courses.total} cursos</strong> diferentes.
          </p>
          <p style={{ marginBottom: '1rem' }}>
            Hay <strong>{stats.instructors.total} instructores</strong> registrados, de los cuales{' '}
            <strong>{stats.instructors.with_classes}</strong> tienen clases asignadas.
          </p>
          <p style={{ marginBottom: '1rem' }}>
            Se dispone de <strong>{stats.rooms.total} aulas</strong> con una capacidad 
            promedio de <strong>{stats.rooms.avg_capacity.toFixed(0)} estudiantes</strong>.
          </p>
          <p>
            El sistema gestiona <strong>{stats.students.total} estudiantes</strong>, 
            de los cuales <strong>{stats.students.enrolled}</strong> están inscritos en clases.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
