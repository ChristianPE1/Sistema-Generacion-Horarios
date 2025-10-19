import { useState, useEffect } from 'react';
import { getScheduleTimetable } from '../services/api';

interface ClassInfo {
  id: number;
  xml_id: number;
  name: string;
  code: string;
  instructors: string[];
  room: string;
  room_capacity: number;
  limit: number;
  students: number;
  start: string;
  end: string;
  duration_min: number;
  time: string;
}

interface TimetableData {
  schedule: {
    id: number;
    name: string;
    description: string;
    fitness_score: number;
    total_assignments: number;
  };
  time_slots: string[];
  days: string[];
  grid: {
    [day: string]: {
      [time: string]: ClassInfo[];
    };
  };
  classes: ClassInfo[];
  stats: {
    total_classes: number;
    classes_by_day: { [day: string]: number };
    max_concurrent_classes: number;
    needs_multiple_views: boolean;
  };
}

interface TimetableViewProps {
  scheduleId: number;
}

function TimetableView({ scheduleId }: TimetableViewProps) {
  const [data, setData] = useState<TimetableData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<string>('Lunes');
  const [selectedClass, setSelectedClass] = useState<ClassInfo | null>(null);

  useEffect(() => {
    loadTimetable();
  }, [scheduleId]);

  const loadTimetable = async () => {
    try {
      setLoading(true);
      const response = await getScheduleTimetable(scheduleId);
      setData(response.data);
      setError(null);
    } catch (err) {
      setError('Error al cargar el horario');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Cargando horario...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {error || 'No se pudo cargar el horario'}
      </div>
    );
  }

  const dayGrid = data.grid[selectedDay] || {};
  const timeSlots = data.time_slots;

  return (
    <div className="space-y-6">
      {/* Header con estadísticas */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">{data.schedule.name}</h2>
            <p className="text-gray-600">{data.schedule.description}</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600">Fitness Score</div>
            <div className="text-2xl font-bold text-green-600">
              {data.schedule.fitness_score.toLocaleString()}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mt-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Total Clases</div>
            <div className="text-2xl font-bold text-blue-600">{data.stats.total_classes}</div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Asignaciones</div>
            <div className="text-2xl font-bold text-purple-600">{data.schedule.total_assignments}</div>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Clases Simultáneas (máx)</div>
            <div className="text-2xl font-bold text-orange-600">{data.stats.max_concurrent_classes}</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Horarios por Día</div>
            <div className="text-2xl font-bold text-green-600">
              {Object.keys(data.grid).length} días
            </div>
          </div>
        </div>

        {data.stats.needs_multiple_views && (
          <div className="mt-4 bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded">
            ℹ️ Este horario tiene muchas clases simultáneas ({data.stats.max_concurrent_classes}). 
            Se recomienda usar pestañas por día para mejor visualización.
          </div>
        )}
      </div>

      {/* Pestañas de días */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="border-b border-gray-200">
          <div className="flex overflow-x-auto">
            {data.days.map(day => (
              <button
                key={day}
                onClick={() => setSelectedDay(day)}
                className={`px-6 py-3 font-medium whitespace-nowrap transition ${
                  selectedDay === day
                    ? 'bg-blue-600 text-white border-b-2 border-blue-600'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {day}
                {data.stats.classes_by_day[day] > 0 && (
                  <span className={`ml-2 px-2 py-1 text-xs rounded ${
                    selectedDay === day ? 'bg-blue-700' : 'bg-gray-200'
                  }`}>
                    {data.stats.classes_by_day[day]}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Grid del horario */}
        <div className="p-6">
          {Object.keys(dayGrid).length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No hay clases programadas para {selectedDay}
            </div>
          ) : (
            <div className="space-y-4">
              {timeSlots.map(time => {
                const classes = dayGrid[time] || [];
                if (classes.length === 0) return null;

                return (
                  <div key={time} className="border-l-4 border-blue-500 pl-4">
                    <div className="font-bold text-lg text-gray-800 mb-2">{time}</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {classes.map((classInfo, idx) => (
                        <div
                          key={`${classInfo.id}-${idx}`}
                          onClick={() => setSelectedClass(classInfo)}
                          className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-blue-500 hover:shadow-md transition cursor-pointer"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <div className="font-bold text-gray-800 flex-1">
                              {classInfo.name}
                            </div>
                            <div className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              {classInfo.code}
                            </div>
                          </div>

                          <div className="space-y-1 text-sm text-gray-600">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">🕒</span>
                              <span>{classInfo.start} - {classInfo.end}</span>
                              <span className="text-xs text-gray-500">
                                ({classInfo.duration_min} min)
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="font-semibold">👨‍🏫</span>
                              <span className="truncate">{classInfo.instructors.join(', ')}</span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="font-semibold">🚪</span>
                              <span>{classInfo.room}</span>
                              <span className="text-xs text-gray-500">
                                (Cap: {classInfo.room_capacity})
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="font-semibold">👥</span>
                              <span>
                                {classInfo.students} / {classInfo.limit} estudiantes
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Modal de detalles de clase */}
      {selectedClass && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedClass(null)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-2xl font-bold text-gray-800">{selectedClass.name}</h3>
              <button
                onClick={() => setSelectedClass(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-600 font-semibold">Código del Curso</div>
                  <div className="text-lg">{selectedClass.code}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 font-semibold">ID de Clase</div>
                  <div className="text-lg">{selectedClass.xml_id}</div>
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-600 font-semibold">Horario</div>
                <div className="text-lg">
                  {selectedClass.start} - {selectedClass.end}
                  <span className="text-sm text-gray-500 ml-2">
                    ({selectedClass.duration_min} minutos)
                  </span>
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-600 font-semibold">Instructores</div>
                <div className="text-lg">
                  {selectedClass.instructors.map((inst, idx) => (
                    <div key={idx} className="text-gray-800">{inst}</div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-600 font-semibold">Aula</div>
                  <div className="text-lg">{selectedClass.room}</div>
                  <div className="text-sm text-gray-500">
                    Capacidad: {selectedClass.room_capacity}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 font-semibold">Estudiantes</div>
                  <div className="text-lg">
                    {selectedClass.students} / {selectedClass.limit}
                  </div>
                  <div className={`text-sm ${
                    selectedClass.students > selectedClass.room_capacity
                      ? 'text-red-600'
                      : 'text-green-600'
                  }`}>
                    {selectedClass.students > selectedClass.room_capacity
                      ? '⚠️ Excede capacidad del aula'
                      : '✓ Dentro de capacidad'}
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedClass(null)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TimetableView;
