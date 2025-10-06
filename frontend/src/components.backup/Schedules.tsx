import { useState, useEffect } from 'react';
import { getSchedules } from '../services/api';
import type { Schedule } from '../types';

function Schedules() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = async () => {
    try {
      setLoading(true);
      const response = await getSchedules();
      setSchedules(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar los horarios');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Cargando horarios...</div>;

  return (
    <div>
      <h2 style={{ marginBottom: '2rem' }}>📅 Horarios Generados</h2>

      {error && <div className="error">{error}</div>}

      <div className="card">
        {schedules.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>No hay horarios generados</h3>
            <p style={{ color: '#7f8c8d', marginBottom: '2rem' }}>
              Los horarios se generarán mediante el algoritmo genético.
              Esta funcionalidad estará disponible próximamente.
            </p>
            <div className="badge badge-warning" style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
              🚧 Módulo de generación en desarrollo
            </div>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Descripción</th>
                  <th>Fitness Score</th>
                  <th>Asignaciones</th>
                  <th>Estado</th>
                  <th>Creado</th>
                </tr>
              </thead>
              <tbody>
                {schedules.map(schedule => (
                  <tr key={schedule.id}>
                    <td><strong>{schedule.name}</strong></td>
                    <td>{schedule.description || '-'}</td>
                    <td>{schedule.fitness_score.toFixed(2)}</td>
                    <td>
                      <span className="badge badge-primary">{schedule.assignment_count || 0}</span>
                    </td>
                    <td>
                      <span className={`badge ${schedule.is_active ? 'badge-success' : 'badge-secondary'}`}>
                        {schedule.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td>{new Date(schedule.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Schedules;
