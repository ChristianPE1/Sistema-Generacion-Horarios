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

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="text-gray-600">Cargando estadísticas...</div>
    </div>
  );
  
  if (error) return (
    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
      {error}
    </div>
  );
  
  if (!stats) return null;

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-800 mb-8">Dashboard del Sistema</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
          <div className="text-sm font-medium text-gray-600 mb-2">Aulas</div>
          <div className="text-4xl font-bold text-gray-900 mb-3">{stats.rooms.total}</div>
          <div className="text-sm text-gray-500">
            <div>Capacidad promedio: {stats.rooms.avg_capacity.toFixed(0)}</div>
            <div>Con restricciones: {stats.rooms.with_constraints}</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
          <div className="text-sm font-medium text-gray-600 mb-2">Instructores</div>
          <div className="text-4xl font-bold text-gray-900 mb-3">{stats.instructors.total}</div>
          <div className="text-sm text-gray-500">
            Con clases asignadas: {stats.instructors.with_classes}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
          <div className="text-sm font-medium text-gray-600 mb-2">Cursos</div>
          <div className="text-4xl font-bold text-gray-900 mb-3">{stats.courses.total}</div>
          <div className="text-sm text-gray-500">
            Con clases: {stats.courses.with_classes}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-yellow-500">
          <div className="text-sm font-medium text-gray-600 mb-2">Clases</div>
          <div className="text-4xl font-bold text-gray-900 mb-3">{stats.classes.total}</div>
          <div className="text-sm text-gray-500">
            <div>Comprometidas: {stats.classes.committed}</div>
            <div>Con instructor: {stats.classes.with_instructor}</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
          <div className="text-sm font-medium text-gray-600 mb-2">Estudiantes</div>
          <div className="text-4xl font-bold text-gray-900 mb-3">{stats.students.total}</div>
          <div className="text-sm text-gray-500">
            Inscritos: {stats.students.enrolled}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-indigo-500">
          <div className="text-sm font-medium text-gray-600 mb-2">Slots de Tiempo</div>
          <div className="text-4xl font-bold text-gray-900 mb-3">{stats.timeslots.total}</div>
          <div className="text-sm text-gray-500">
            Horarios disponibles
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Resumen del Sistema</h3>
        <div className="space-y-3 text-gray-700">
          <p>
            El sistema cuenta con <strong className="text-gray-900">{stats.classes.total} clases</strong> distribuidas 
            en <strong className="text-gray-900">{stats.courses.total} cursos</strong> diferentes.
          </p>
          <p>
            Hay <strong className="text-gray-900">{stats.instructors.total} instructores</strong> registrados, de los cuales{' '}
            <strong className="text-gray-900">{stats.instructors.with_classes}</strong> tienen clases asignadas.
          </p>
          <p>
            Se dispone de <strong className="text-gray-900">{stats.rooms.total} aulas</strong> con una capacidad 
            promedio de <strong className="text-gray-900">{stats.rooms.avg_capacity.toFixed(0)} estudiantes</strong>.
          </p>
          <p>
            El sistema gestiona <strong className="text-gray-900">{stats.students.total} estudiantes</strong>, 
            de los cuales <strong className="text-gray-900">{stats.students.enrolled}</strong> están inscritos en clases.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
