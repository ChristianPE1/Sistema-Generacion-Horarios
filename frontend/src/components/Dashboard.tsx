import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSavedSchedules } from '../services/api';
import { Calendar, Eye, Clock, Plus, ArrowRight, Sparkles, CheckCircle2, AlertCircle, Dna } from 'lucide-react';
import type { SavedSchedule } from '../types';

function Dashboard() {
  const [recentSchedules, setRecentSchedules] = useState<SavedSchedule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await getSavedSchedules();
      if (response.data.success) {
        setRecentSchedules(response.data.schedules || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          <p className="text-gray-500">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 p-6">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl shadow-lg mb-4">
          <Calendar className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Sistema de Generación de Horarios
        </h1>
        <p className="text-gray-600">
          Genera horarios universitarios optimizados usando <strong>Algoritmo Genético + Greedy</strong>
        </p>
      </div>

      {/* Main Actions */}
      <main className="grid sm:grid-cols-2 gap-4 max-w-xl mx-auto">
        <Link
          to="/schedules"
          className="group flex flex-col items-center p-6 bg-blue-600 rounded-2xl text-white shadow-lg hover:shadow-xl transition-all hover:-translate-y-1"
        >
          <Sparkles className="h-10 w-10 mb-3 group-hover:scale-110 transition-transform" />
          <span className="text-lg font-semibold">Generar Horario</span>
          <span className="text-sm text-blue-100 mt-1">Sistema Híbrido AG+Greedy</span>
        </Link>
        
        <Link
          to="/schedule-viewer"
          className="group flex flex-col items-center p-6 bg-purple-600 rounded-2xl text-white shadow-lg hover:shadow-xl transition-all hover:-translate-y-1"
        >
          <Eye className="h-10 w-10 mb-3 group-hover:scale-110 transition-transform" />
          <span className="text-lg font-semibold">Ver Horarios</span>
          <span className="text-sm text-purple-100 mt-1">Visualizar calendario</span>
        </Link>
      </main>

      {/* Recent Schedules */}
      <section className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Dna className="h-5 w-5 text-indigo-600" />
              <h2 className="text-lg font-semibold text-gray-900">Horarios Generados</h2>
            </div>
            <Link 
              to="/schedule-viewer" 
              className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
            >
              Ver todos <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          
          <div className="divide-y divide-gray-100">
            {recentSchedules.length === 0 ? (
              <div className="p-8 text-center">
                <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No hay horarios generados aún</p>
                <Link 
                  to="/schedules" 
                  className="inline-flex items-center gap-2 mt-4 text-blue-600 hover:text-blue-700 font-medium"
                >
                  <Plus className="h-4 w-4" /> Generar primer horario
                </Link>
              </div>
            ) : (
              recentSchedules.slice(0, 5).map((schedule) => (
                <Link
                  key={schedule.id}
                  to={`/schedule-viewer?id=${schedule.id}`}
                  className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${
                      schedule.conflict_count > 0 ? 'bg-red-100' : 'bg-green-100'
                    }`}>
                      {schedule.conflict_count > 0 ? (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      ) : (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{schedule.name}</p>
                      <p className="text-sm text-gray-500">
                        {schedule.dataset} • {schedule.classes_assigned} clases
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">
                      Fitness: {schedule.fitness_score.toFixed(0)}
                    </p>
                    <p className="text-xs text-gray-500 flex items-center gap-1 justify-end">
                      <Clock className="h-3 w-3" />
                      {new Date(schedule.created_at).toLocaleDateString('es-ES', {
                        day: 'numeric',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </section>

      {/* Algorithm Info */}
      <footer className="max-w-4xl mx-auto">
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Dna className="h-5 w-5 text-indigo-600" />
            Sistema Híbrido: Greedy + Algoritmo Genético
          </h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
            <div>
              <p className="font-medium text-gray-800 mb-1">Fase 1: Inicialización Greedy</p>
              <p>Genera una solución inicial válida asignando clases a aulas de forma óptima local.</p>
            </div>
            <div>
              <p className="font-medium text-gray-800 mb-1">Fase 2: Refinamiento Genético</p>
              <p>Evoluciona la población mediante selección, cruce y mutación para optimizar la distribución.</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Dashboard;
