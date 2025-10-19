import { useState, useEffect } from 'react';
import { getSchedules } from '../services/api';
import type { Schedule } from '../types';
import TimetableView from './TimetableView';

function Schedules() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedScheduleId, setSelectedScheduleId] = useState<number | null>(null);

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

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="text-gray-600">Cargando horarios...</div>
    </div>
  );

  // Si hay un horario seleccionado, mostrar la vista de horario
  if (selectedScheduleId) {
    return (
      <div>
        <button
          onClick={() => setSelectedScheduleId(null)}
          className="mb-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition flex items-center gap-2"
        >
          <span>←</span> Volver a lista de horarios
        </button>
        <TimetableView scheduleId={selectedScheduleId} />
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-8">Horarios Generados</h2>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md p-6">
        {schedules.length === 0 ? (
          <div className="text-center py-12">
            <h3 className="text-xl font-bold text-gray-800 mb-4">No hay horarios generados</h3>
            <p className="text-gray-600 mb-6">
              Los horarios se generarán mediante el algoritmo genético.
              Esta funcionalidad estará disponible próximamente.
            </p>
            <div className="inline-block bg-yellow-100 text-yellow-800 px-4 py-2 rounded text-sm font-medium">
              Módulo de generación en desarrollo
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fitness Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asignaciones</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creado</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {schedules.map(schedule => (
                  <tr key={schedule.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{schedule.name}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{schedule.description || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className="font-bold text-green-600">
                        {schedule.fitness_score.toLocaleString()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">
                        {schedule.assignment_count || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded ${schedule.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {schedule.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(schedule.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedScheduleId(schedule.id)}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                      >
                        Ver Horario
                      </button>
                    </td>
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
