import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { type GeneratedSchedule, getSavedSchedules, getSavedSchedule } from '../services/api';
import { Building2, User, Calendar, AlertCircle, ArrowLeft, ChevronLeft, ChevronRight, Download, RefreshCw } from 'lucide-react';
//import * as XLSX from 'xlsx';
import * as XLSX from 'xlsx-js-style';


type ViewMode = 'room' | 'instructor' | 'year';

interface ScheduleBlock {
  day: string;
  block: number;
  start: string;
  end: string;
}

interface Assignment {
  class_id: string;
  class_name: string;
  class_type: string;
  year: number;
  room: { id: string; type: string };
  instructor: { id: string; name: string };
  schedule: ScheduleBlock[];
}

interface SavedScheduleOption {
  id: number;
  name: string;
  dataset: string;
  created_at: string;
}

function ScheduleViewer() {
  const navigate = useNavigate();
  const [schedule, setSchedule] = useState<GeneratedSchedule | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('room');
  const [selectedFilter, setSelectedFilter] = useState<string>('');
  const [savedSchedules, setSavedSchedules] = useState<SavedScheduleOption[]>([]);
  const [currentScheduleId, setCurrentScheduleId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  // Detectar días disponibles del horario
  const availableDays = useMemo(() => {
    if (!schedule) return ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'];
    
    const daysSet = new Set<string>();
    schedule.assignments.forEach((a: Assignment) => {
      a.schedule.forEach((s: ScheduleBlock) => {
        daysSet.add(s.day);
      });
    });
    
    const allDays = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'];
    return allDays.filter(d => daysSet.has(d));
  }, [schedule]);

  const blocks = Array.from({ length: 13 }, (_, i) => i);

  useEffect(() => {
    loadSavedSchedules();
    const stored = localStorage.getItem('generatedSchedule');
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as GeneratedSchedule;
        setSchedule(parsed);
      } catch (e) {
        console.error('Error parsing schedule:', e);
      }
    }
  }, []);

  const loadSavedSchedules = async () => {
    try {
      const response = await getSavedSchedules();
      if (response.data.success) {
        setSavedSchedules(response.data.schedules.map(s => ({
          id: s.id,
          name: s.name,
          dataset: s.dataset,
          created_at: s.created_at
        })));
      }
    } catch (err) {
      console.error('Error loading saved schedules:', err);
    }
  };

  const loadScheduleById = async (id: number) => {
    setLoading(true);
    try {
      const response = await getSavedSchedule(id);
      if (response.data.success) {
        setSchedule(response.data.schedule);
        setCurrentScheduleId(id);
        localStorage.setItem('generatedSchedule', JSON.stringify(response.data.schedule));
      }
    } catch (err) {
      console.error('Error loading schedule:', err);
    } finally {
      setLoading(false);
    }
  };

  // Extraer opciones de filtro según el modo
  const filterOptions = useMemo(() => {
    if (!schedule) return [];
    
    const options = new Set<string>();
    schedule.assignments.forEach((a: Assignment) => {
      if (viewMode === 'room') {
        options.add(a.room.id);
      } else if (viewMode === 'instructor') {
        options.add(a.instructor.name);
      } else if (viewMode === 'year') {
        options.add(a.year.toString());
      }
    });
    
    return Array.from(options).sort((a, b) => {
      if (viewMode === 'year') return parseInt(a) - parseInt(b);
      return a.localeCompare(b);
    });
  }, [schedule, viewMode]);

  // Establecer filtro por defecto cuando cambia el modo
  useEffect(() => {
    if (filterOptions.length > 0 && !filterOptions.includes(selectedFilter)) {
      setSelectedFilter(filterOptions[0]);
    }
  }, [filterOptions, viewMode]);

  // Navegación por flechas
  const currentIndex = filterOptions.indexOf(selectedFilter);
  const canGoPrev = currentIndex > 0;
  const canGoNext = currentIndex < filterOptions.length - 1;

  const goToPrev = () => {
    if (canGoPrev) {
      setSelectedFilter(filterOptions[currentIndex - 1]);
    }
  };

  const goToNext = () => {
    if (canGoNext) {
      setSelectedFilter(filterOptions[currentIndex + 1]);
    }
  };

  // Filtrar asignaciones
  const filteredAssignments = useMemo(() => {
    if (!schedule || !selectedFilter) return [];
    
    return schedule.assignments.filter((a: Assignment) => {
      if (viewMode === 'room') return a.room.id === selectedFilter;
      if (viewMode === 'instructor') return a.instructor.name === selectedFilter;
      if (viewMode === 'year') return a.year.toString() === selectedFilter;
      return true;
    });
  }, [schedule, selectedFilter, viewMode]);

  // Obtener asignaciones en una celda específica
  const getAssignmentsAt = (day: string, block: number): Assignment[] => {
    return filteredAssignments.filter((a: Assignment) => 
      a.schedule.some((s: ScheduleBlock) => s.day === day && s.block === block)
    );
  };

  const getBlockTime = (block: number) => {
    const startMinutes = 7 * 60 + block * 60;
    const h = Math.floor(startMinutes / 60);
    const m = startMinutes % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
  };

  // Exportar TODAS las aulas a Excel (cada aula = 1 hoja)
  const exportToExcel = () => {
    if (!schedule) return;

    const wb = XLSX.utils.book_new();

    // Obtener todas las aulas
    const allRooms = new Set<string>();
    schedule.assignments.forEach((a: Assignment) => {
      allRooms.add(a.room.id);
    });

    const sortedRooms = Array.from(allRooms).sort((a, b) => a.localeCompare(b));

    sortedRooms.forEach(roomId => {
      const wsData: string[][] = [];

      // Header
      wsData.push([
        'Hora',
        ...availableDays.map(d => d.charAt(0).toUpperCase() + d.slice(1))
      ]);

      const roomAssignments = schedule.assignments.filter(
        (a: Assignment) => a.room.id === roomId
      );

      // Rows
      blocks.forEach(block => {
        const row = [getBlockTime(block)];
        availableDays.forEach(day => {
          const assignments = roomAssignments.filter((a: Assignment) =>
            a.schedule.some(
              (s: ScheduleBlock) => s.day === day && s.block === block
            )
          );

          const cellContent = assignments
            .map(a => `${a.class_name} (${a.instructor.name})`)
            .join('\n');

          row.push(cellContent);
        });
        wsData.push(row);
      });

      const ws = XLSX.utils.aoa_to_sheet(wsData);

      // Ancho de columnas
      ws['!cols'] = [
        { wch: 10 }, // Hora
        ...availableDays.map(() => ({ wch: 30 }))
      ];

      // Altura de filas (header + filas normales)
      ws['!rows'] = wsData.map((_, i) => ({
        hpt: i === 0 ? 28 : 55
      }));

      // Estilos
      for (let r = 0; r < wsData.length; r++) {
        for (let c = 0; c < wsData[r].length; c++) {
          const cellRef = XLSX.utils.encode_cell({ r, c });
          if (!ws[cellRef]) continue;

          const isHeader = r === 0;

          ws[cellRef].s = {
            alignment: {
              horizontal: 'center',
              vertical: 'center',
              wrapText: true
            },
            font: {
              bold: isHeader
            },
            border: {
              top: { style: 'thin' },
              bottom: { style: 'thin' },
              left: { style: 'thin' },
              right: { style: 'thin' }
            }
          };
        }
      }

      // Nombre de hoja
      const sheetName = `Aula ${roomId}`.substring(0, 31);
      XLSX.utils.book_append_sheet(wb, ws, sheetName);
    });

    // Guardar archivo
    const filename = schedule.name
      ? `${schedule.name}_todas_aulas.xlsx`
      : 'horario_completo.xlsx';

    XLSX.writeFile(wb, filename);
  };


  const typeColors: Record<string, string> = {
    teoria: 'bg-blue-100 border-blue-300 text-blue-800',
    practica: 'bg-green-100 border-green-300 text-green-800',
    laboratorio: 'bg-purple-100 border-purple-300 text-purple-800'
  };

  if (!schedule) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-8 text-center">
          <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-800 mb-2">No hay horario generado</h2>
          <p className="text-gray-600 mb-6">
            Primero debe generar un horario desde la sección correspondiente.
          </p>
          <button
            onClick={() => navigate('/schedules')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
          >
            <Calendar className="h-5 w-5" />
            Ir a Generar Horario
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header con stats */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/schedules')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </button>
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">{schedule.name || 'Horario Generado'}</h1>
                {savedSchedules.length > 0 && (
                  <div className="flex items-center gap-2">
                    <select
                      value={currentScheduleId || ''}
                      onChange={(e) => {
                        const id = parseInt(e.target.value);
                        if (id) loadScheduleById(id);
                      }}
                      disabled={loading}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Horario actual (temporal)</option>
                      {savedSchedules.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name} - {new Date(s.created_at).toLocaleDateString()}
                        </option>
                      ))}
                    </select>
                    {loading && <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />}
                  </div>
                )}
              </div>
              <p className="text-sm text-gray-500">{schedule.dataset}</p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className={`rounded-lg p-4 border ${schedule.conflict_count > 0 ? 'bg-red-50 border-red-100' : 'bg-green-50 border-green-100'}`}>
            <div className={`flex items-center gap-2 text-sm font-medium ${schedule.conflict_count > 0 ? 'text-red-600' : 'text-green-600'}`}>
              <AlertCircle className="h-4 w-4" />
              Conflictos
            </div>
            <div className={`text-2xl font-bold mt-1 ${schedule.conflict_count > 0 ? 'text-red-700' : 'text-green-700'}`}>
              {schedule.conflict_count}
            </div>
          </div>
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
            <div className="flex items-center gap-2 text-blue-600 text-sm font-medium">
              <Calendar className="h-4 w-4" />
              Clases Asignadas
            </div>
            <div className="text-2xl font-bold text-blue-700 mt-1">
              {schedule.classes_assigned}/{schedule.classes_total}
            </div>
          </div>
        </div>

        {/* View Mode Toggle & Filter */}
        <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
          <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setViewMode('room')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                viewMode === 'room' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Building2 className="h-4 w-4" />
              Por Aula
            </button>
            <button
              onClick={() => setViewMode('instructor')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                viewMode === 'instructor' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <User className="h-4 w-4" />
              Por Instructor
            </button>
            <button
              onClick={() => setViewMode('year')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                viewMode === 'year' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Calendar className="h-4 w-4" />
              Por Año
            </button>
          </div>

          {/* Navegación por flechas */}
          <div className="flex items-center gap-2">
            <button
              onClick={goToPrev}
              disabled={!canGoPrev}
              className={`p-2 rounded-lg border transition-colors ${
                canGoPrev 
                  ? 'border-gray-300 hover:bg-gray-100 text-gray-700' 
                  : 'border-gray-200 text-gray-300 cursor-not-allowed'
              }`}
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[200px]"
            >
              {filterOptions.map((option) => (
                <option key={option} value={option}>
                  {viewMode === 'room' && `Aula ${option}`}
                  {viewMode === 'instructor' && option}
                  {viewMode === 'year' && `${option}° Año`}
                </option>
              ))}
            </select>
            
            <button
              onClick={goToNext}
              disabled={!canGoNext}
              className={`p-2 rounded-lg border transition-colors ${
                canGoNext 
                  ? 'border-gray-300 hover:bg-gray-100 text-gray-700' 
                  : 'border-gray-200 text-gray-300 cursor-not-allowed'
              }`}
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>

          <div className="text-sm text-gray-500">
            {filteredAssignments.length} clases en esta vista
          </div>

          {/* Botón exportar Excel - TODAS las aulas */}
          <button
            onClick={exportToExcel}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
          >
            <Download className="h-4 w-4" />
            Exportar Todas las Aulas (Excel)
          </button>
        </div>
      </div>

      {/* Timetable Grid */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse min-w-[800px]">
            <thead>
              <tr className="bg-gray-50">
                <th className="border-b border-r border-gray-200 p-3 text-left text-sm font-semibold text-gray-600 w-20">
                  Hora
                </th>
                {availableDays.map(day => (
                  <th key={day} className="border-b border-gray-200 p-3 text-center text-sm font-semibold text-gray-600 capitalize">
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {blocks.map(block => (
                <tr key={block} className="hover:bg-gray-50/50">
                  <td className="border-b border-r border-gray-200 p-2 text-center text-sm font-medium text-gray-500 bg-gray-50">
                    {getBlockTime(block)}
                  </td>
                  {availableDays.map(day => {
                    const assignments = getAssignmentsAt(day, block);
                    return (
                      <td 
                        key={`${day}-${block}`} 
                        className="border-b border-gray-200 p-1 align-top min-h-[60px]"
                      >
                        {assignments.map((a, idx) => (
                          <div
                            key={`${a.class_id}-${idx}`}
                            className={`text-xs p-2 mb-1 rounded-lg border ${typeColors[a.class_type] || 'bg-gray-100 border-gray-300'}`}
                            title={`${a.class_name}\nAula: ${a.room.id}\nProfesor: ${a.instructor.name}`}
                          >
                            <div className="font-semibold truncate leading-tight">
                              {a.class_name.length > 25 ? a.class_name.substring(0, 25) + '...' : a.class_name}
                            </div>
                            <div className="text-[10px] opacity-80 mt-0.5 flex justify-between">
                              <span>{viewMode !== 'room' ? `Aula ${a.room.id}` : a.instructor.name}</span>
                              {viewMode === 'room' && <span>{a.year}°</span>}
                            </div>
                          </div>
                        ))}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap gap-4 items-center justify-center">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-blue-100 border border-blue-300"></div>
            <span className="text-sm text-gray-600">Teoría</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-green-100 border border-green-300"></div>
            <span className="text-sm text-gray-600">Práctica</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-purple-100 border border-purple-300"></div>
            <span className="text-sm text-gray-600">Laboratorio</span>
          </div>
        </div>
      </div>

      {/* Unassigned Classes */}
      {schedule.unassigned && schedule.unassigned.length > 0 && (
        <div className="bg-red-50 rounded-xl border border-red-200 p-6">
          <h3 className="text-lg font-semibold text-red-800 mb-4 flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Clases sin asignar ({schedule.unassigned.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {schedule.unassigned.map((className: string, idx: number) => (
              <div key={idx} className="bg-white rounded-lg p-3 text-sm text-red-700 border border-red-200">
                {className}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ScheduleViewer;
