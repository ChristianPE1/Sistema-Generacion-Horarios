import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDashboardStats, getSchedules } from '../services/api';
import type { DashboardStats, Schedule } from '../types';
import { 
  Calendar, 
  Upload, 
  Eye, 
  Building2, 
  Users, 
  BookOpen, 
  GraduationCap,
  Clock,
  Plus,
  ArrowRight,
  Sparkles,
  FileText,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentSchedules, setRecentSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasData, setHasData] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsResponse, schedulesResponse] = await Promise.all([
        getDashboardStats().catch(() => null),
        getSchedules(1, 5).catch(() => null)
      ]);
      
      if (statsResponse?.data) {
        setStats(statsResponse.data);
        setHasData(statsResponse.data.classes.total > 0);
      }
      
      if (schedulesResponse?.data) {
        setRecentSchedules(schedulesResponse.data.results || []);
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

  // Vista cuando no hay datos importados
  if (!hasData) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center px-4">
        <div className="max-w-3xl w-full text-center">
          {/* Hero Section */}
          <div className="mb-12">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-600 rounded-2xl shadow-lg mb-6">
              <Calendar className="h-10 w-10 text-white" />
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
              Sistema de Generación de Horarios
            </h1>
            <p className="text-lg text-gray-600 max-w-xl mx-auto">
              Genera horarios universitarios optimizados automáticamente usando algoritmos constructivos.
            </p>
          </div>

          {/* Main Actions */}
          <div className="grid sm:grid-cols-2 gap-4 mb-12 max-w-xl mx-auto">
            {/* Botón Importar - Deshabilitado en local */}
            <div
              className="group flex flex-col items-center p-6 bg-gray-200 rounded-2xl text-gray-400 cursor-not-allowed opacity-60"
              title="Función no disponible en modo local"
            >
              <Upload className="h-10 w-10 mb-3" />
              <span className="text-lg font-semibold">Importar Datos XML</span>
              <span className="text-sm text-gray-400 mt-1">No disponible en local</span>
            </div>
            
            <Link
              to="/schedules"
              className="group flex flex-col items-center p-6 bg-blue-600 rounded-2xl text-white shadow-lg hover:shadow-xl transition-all hover:-translate-y-1"
            >
              <Eye className="h-10 w-10 mb-3 group-hover:scale-110 transition-transform" />
              <span className="text-lg font-semibold">Generar Horario</span>
              <span className="text-sm text-blue-100 mt-1">Comienza aquí</span>
            </Link>
          </div>

          {/* Info Section */}
          <div className="bg-blue-50 rounded-2xl p-6 sm:p-8 text-left">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Formato de archivo compatible
                </h3>
                <p className="text-gray-600 mb-4">
                  Este sistema usa archivos XML con el formato personalizado v3.0 para definir aulas, instructores y clases.
                </p>
                <div className="bg-white rounded-xl p-4 border border-blue-100">
                  <p className="text-sm font-medium text-gray-700 mb-2">Estructura esperada del XML:</p>
                  <pre className="text-xs bg-gray-50 p-3 rounded-lg overflow-x-auto text-gray-600">
{`<timetable version="3.0" type="escuela">
  <rooms>
    <room id="A101" capacity="40" type="aula"/>
    <room id="LAB1" capacity="25" type="laboratorio"/>
  </rooms>
  <instructors>
    <instructor id="1" name="Juan Pérez" status="TC"/>
  </instructors>
  <classes>
    <class id="1" name="Programación I" code="CS101" 
           students="35" instructor="1" type="teoria" 
           hours="2" year="1"/>
  </classes>
  <config days="lunes,martes,miercoles,jueves,viernes" 
          block_duration="50" break_duration="10"
          start_time="07:00" end_time="20:00" 
          max_consecutive="3"/>
</timetable>`}
                  </pre>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                    <CheckCircle2 className="h-4 w-4" /> Aulas con capacidad y tipo
                  </span>
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                    <CheckCircle2 className="h-4 w-4" /> Clases con horas y año
                  </span>
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                    <CheckCircle2 className="h-4 w-4" /> Instructores
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Vista cuando hay datos
  return (
    <div className="space-y-8">
      {/* Header con acciones rápidas */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Panel de Control</h1>
          <p className="text-gray-500 mt-1">Resumen general del sistema</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            to="/schedules"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
          >
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">Nuevo Horario</span>
            <span className="sm:hidden">Nuevo</span>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={Building2}
            label="Aulas"
            value={stats.rooms.total}
            sublabel={`Capacidad prom: ${stats.rooms.avg_capacity.toFixed(0)}`}
            color="blue"
          />
          <StatCard
            icon={Users}
            label="Instructores"
            value={stats.instructors.total}
            sublabel={`${stats.instructors.with_classes} con clases`}
            color="green"
          />
          <StatCard
            icon={BookOpen}
            label="Cursos"
            value={stats.courses.total}
            sublabel={`${stats.courses.with_classes} con clases`}
            color="purple"
          />
          <StatCard
            icon={GraduationCap}
            label="Clases"
            value={stats.classes.total}
            sublabel={`${stats.classes.with_instructor} con instructor`}
            color="amber"
          />
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Horarios Recientes */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Horarios Recientes</h2>
            <Link to="/schedules" className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
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
                  <Sparkles className="h-4 w-4" /> Generar primer horario
                </Link>
              </div>
            ) : (
              recentSchedules.map((schedule) => (
                <Link
                  key={schedule.id}
                  to="/schedules"
                  className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${schedule.status === 'generating' ? 'bg-amber-100' : schedule.conflict_count && schedule.conflict_count > 0 ? 'bg-red-100' : 'bg-green-100'}`}>
                      {schedule.status === 'generating' ? (
                        <Clock className="h-5 w-5 text-amber-600 animate-pulse" />
                      ) : schedule.conflict_count && schedule.conflict_count > 0 ? (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      ) : (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{schedule.name}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(schedule.created_at).toLocaleDateString('es-ES', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric'
                        })}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">{schedule.fitness_score.toLocaleString()}</p>
                    <p className="text-sm text-gray-500">
                      {schedule.conflict_count || 0} conflictos
                    </p>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Acciones Rápidas */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Acciones Rápidas</h2>
            <div className="space-y-3">
              <Link
                to="/schedules"
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-all group"
              >
                <div className="p-2 bg-indigo-100 rounded-lg group-hover:bg-indigo-200 transition-colors">
                  <Sparkles className="h-5 w-5 text-indigo-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Generar Horario</p>
                  <p className="text-sm text-gray-500">Crear nuevo horario optimizado</p>
                </div>
              </Link>
              
              <Link
                to="/schedule-viewer"
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-all group"
              >
                <div className="p-2 bg-purple-100 rounded-lg group-hover:bg-purple-200 transition-colors">
                  <Eye className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Visualizar Horarios</p>
                  <p className="text-sm text-gray-500">Ver calendario interactivo</p>
                </div>
              </Link>
              
              <Link
                to="/import"
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-green-300 hover:bg-green-50 transition-all group"
              >
                <div className="p-2 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
                  <Upload className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Importar Datos</p>
                  <p className="text-sm text-gray-500">Cargar nuevo archivo XML</p>
                </div>
              </Link>
            </div>
          </div>

          {/* Info Card */}
          {stats && (
            <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
              <h3 className="font-semibold mb-2">Estado del Sistema</h3>
              <p className="text-sm text-indigo-100 mb-4">
                Tienes {stats.classes.total} clases para programar en {stats.rooms.total} aulas disponibles.
              </p>
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4" />
                <span>{stats.timeslots.total} slots de tiempo disponibles</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Componente para las tarjetas de estadísticas
interface StatCardProps {
  icon: React.ElementType;
  label: string;
  value: number;
  sublabel: string;
  color: 'blue' | 'green' | 'purple' | 'amber';
}

function StatCard({ icon: Icon, label, value, sublabel, color }: StatCardProps) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    green: 'bg-green-50 text-green-600 border-green-100',
    purple: 'bg-purple-50 text-purple-600 border-purple-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100'
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
        <span className="text-sm font-medium text-gray-600">{label}</span>
      </div>
      <p className="text-2xl sm:text-3xl font-bold text-gray-900">{value.toLocaleString()}</p>
      <p className="text-sm text-gray-500 mt-1">{sublabel}</p>
    </div>
  );
}

export default Dashboard;
