import { useState, useEffect } from 'react';
import { getSchedules, generateSchedule, updateSchedule, deleteSchedule, exportScheduleExcel } from '../services/api';
import type { Schedule } from '../types';
import type { PaginatedResponse } from '../services/api';
import Pagination from './Pagination';
import ScheduleViewer from './ScheduleViewer';
import * as XLSX from 'xlsx';

function Schedules() {
  const [paginatedData, setPaginatedData] = useState<PaginatedResponse<Schedule> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedScheduleId, setSelectedScheduleId] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  
  // Modals state
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  
  // Action state
  const [generating, setGenerating] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [exporting, setExporting] = useState<number | null>(null);
  const [scheduleToEdit, setScheduleToEdit] = useState<Schedule | null>(null);
  const [scheduleToDelete, setScheduleToDelete] = useState<Schedule | null>(null);

  const [generateFormData, setGenerateFormData] = useState({
    name: '',
    description: '',
    population_size: 100,
    generations: 200,
    mutation_rate: 0.1,
    crossover_rate: 0.8
  });

  const [editFormData, setEditFormData] = useState({
    name: '',
    description: ''
  });

  useEffect(() => {
    loadSchedules(currentPage);
  }, [currentPage]);

  // Polling para actualizar estado de generación
  useEffect(() => {
    let interval: any;
    const hasGenerating = paginatedData?.results.some(s => s.status === 'generating');
    
    if (hasGenerating) {
      interval = setInterval(() => {
        loadSchedules(currentPage, true);
      }, 3000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [paginatedData, currentPage]);

  const loadSchedules = async (page: number, background = false) => {
    try {
      if (!background) setLoading(true);
      const response = await getSchedules(page, 20);
      setPaginatedData(response.data);
      setError(null);
    } catch (err) {
      if (!background) setError('Error al cargar los horarios');
      console.error(err);
    } finally {
      if (!background) setLoading(false);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setGenerating(true);
      await generateSchedule(generateFormData);
      setShowGenerateModal(false);
      setGenerateFormData({
        name: '',
        description: '',
        population_size: 100,
        generations: 200,
        mutation_rate: 0.1,
        crossover_rate: 0.8
      });
      await loadSchedules(1);
      setCurrentPage(1);
    } catch (err) {
      setError('Error al generar el horario');
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleEditClick = (schedule: Schedule) => {
    setScheduleToEdit(schedule);
    setEditFormData({
      name: schedule.name,
      description: schedule.description || ''
    });
    setShowEditModal(true);
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scheduleToEdit) return;

    try {
      setProcessing(true);
      await updateSchedule(scheduleToEdit.id, editFormData);
      setShowEditModal(false);
      setScheduleToEdit(null);
      await loadSchedules(currentPage);
    } catch (err) {
      setError('Error al actualizar el horario');
      console.error(err);
    } finally {
      setProcessing(false);
    }
  };

  const handleDeleteClick = (schedule: Schedule) => {
    setScheduleToDelete(schedule);
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = async () => {
    if (!scheduleToDelete) return;

    try {
      setProcessing(true);
      await deleteSchedule(scheduleToDelete.id);
      setShowDeleteModal(false);
      setScheduleToDelete(null);
      // Si es el último elemento de la página y no es la primera página, ir a la anterior
      if (paginatedData?.results.length === 1 && currentPage > 1) {
        setCurrentPage(prev => prev - 1);
      } else {
        await loadSchedules(currentPage);
      }
    } catch (err) {
      setError('Error al eliminar el horario');
      console.error(err);
    } finally {
      setProcessing(false);
    }
  };

  const handleExportExcel = async (schedule: Schedule) => {
    try {
      setExporting(schedule.id);
      setError(null);

      // Obtener datos del backend
      const response = await exportScheduleExcel(schedule.id);
      const data = response.data;

      // Crear nuevo libro de Excel
      const wb = XLSX.utils.book_new();

      // Días de la semana
      const days = data.days || ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

      // Procesar cada aula (cada una será una hoja)
      for (const roomData of data.rooms) {
        const sheetData: any[][] = [];

        // Encabezado: primera fila con nombre de aula y capacidad
        sheetData.push([`${roomData.room_name} (Capacidad: ${roomData.capacity})`]);
        sheetData.push([]); // Fila vacía

        // Encabezado de columnas: Hora | Lun | Mar | Mie | Jue | Vie | Sab | Dom
        const headerRow = ['Hora', ...days];
        sheetData.push(headerRow);

        // Recolectar todas las horas únicas
        const allHours = new Set<string>();
        for (const day of days) {
          const daySchedule = roomData.schedule[day];
          if (daySchedule) {
            Object.keys(daySchedule).forEach(hour => allHours.add(hour));
          }
        }

        // Ordenar horas
        const sortedHours = Array.from(allHours).sort();

        // Crear filas para cada hora
        for (const hour of sortedHours) {
          const row: any[] = [hour];

          for (const day of days) {
            const daySchedule = roomData.schedule[day];
            const classes = daySchedule?.[hour] || [];

            if (classes.length === 0) {
              row.push('');
            } else if (classes.length === 1) {
              // Una sola clase
              const cls = classes[0];
              const instructors = cls.instructors.join(', ') || 'Sin instructor';
              row.push(`${cls.name}\n${instructors}\n${cls.start}-${cls.end}`);
            } else {
              // Múltiples clases (conflicto)
              const classInfo = classes.map(cls => {
                const instructors = cls.instructors.join(', ') || 'Sin instructor';
                return `${cls.name} (${instructors}) ${cls.start}-${cls.end}`;
              }).join('\n---\n');
              row.push(classInfo);
            }
          }

          sheetData.push(row);
        }

        // Crear hoja de cálculo
        const ws = XLSX.utils.aoa_to_sheet(sheetData);

        // Ajustar ancho de columnas
        ws['!cols'] = [
          { wch: 12 }, // Hora
          ...days.map(() => ({ wch: 30 })) // Días (más ancho para mejor lectura)
        ];

        // Aplicar formato a todas las celdas: centrado y ajuste de texto
        const range = XLSX.utils.decode_range(ws['!ref'] || 'A1');
        for (let R = range.s.r; R <= range.e.r; ++R) {
          for (let C = range.s.c; C <= range.e.c; ++C) {
            const cellAddress = XLSX.utils.encode_cell({ r: R, c: C });
            if (!ws[cellAddress]) continue;
            
            // Inicializar estilo si no existe
            if (!ws[cellAddress].s) ws[cellAddress].s = {};
            
            // Aplicar alineación centrada y ajuste de texto
            ws[cellAddress].s = {
              alignment: {
                vertical: 'center',
                horizontal: 'center',
                wrapText: true
              }
            };
            
            // Hacer encabezados más notorios (negrita, fondo gris)
            if (R === 2) { // Fila de encabezado (Hora | Lun | Mar | ...)
              ws[cellAddress].s = {
                ...ws[cellAddress].s,
                font: { bold: true },
                fill: { fgColor: { rgb: 'E0E0E0' } },
                alignment: {
                  vertical: 'center',
                  horizontal: 'center',
                  wrapText: true
                }
              };
            }
          }
        }

        // Agregar hoja al libro (nombre de hoja limitado a 31 caracteres)
        const sheetName = roomData.room_name.substring(0, 31);
        XLSX.utils.book_append_sheet(wb, ws, sheetName);
      }

      // Generar archivo y descargar
      const fileName = `${data.schedule_name.replace(/[^a-zA-Z0-9]/g, '_')}.xlsx`;
      XLSX.writeFile(wb, fileName);

    } catch (err: any) {
      console.error('Error al exportar a Excel:', err);
      setError(`Error al exportar: ${err.response?.data?.detail || err.message || 'Error desconocido'}`);
    } finally {
      setExporting(null);
    }
  };

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="text-gray-600">Cargando horarios...</div>
    </div>
  );

  if (selectedScheduleId) {
    return (
      <div>
        <button
          onClick={() => setSelectedScheduleId(null)}
          className="mb-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition flex items-center gap-2"
        >
          <span>←</span> Volver a lista de horarios
        </button>
        <ScheduleViewer scheduleId={selectedScheduleId} />
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold text-gray-800">Horarios Generados</h2>
        <button
          onClick={() => setShowGenerateModal(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center gap-2"
        >
          <span>⚙️</span> Generar Nuevo Horario
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md p-6">
        {!paginatedData?.results.length ? (
          <div className="text-center py-12">
            <h3 className="text-xl font-bold text-gray-800 mb-4">No hay horarios generados</h3>
            <p className="text-gray-600 mb-6">
              Utiliza el botón "Generar Nuevo Horario" para crear una nueva distribución de clases.
            </p>
          </div>
        ) : (
          <>
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
                  {paginatedData.results.map(schedule => (
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
                        {schedule.status === 'generating' ? (
                          <span className="px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-800 flex items-center gap-1 w-fit">
                            <span className="animate-spin">↻</span> Generando
                          </span>
                        ) : schedule.status === 'failed' ? (
                          <span className="px-2 py-1 text-xs rounded bg-red-100 text-red-800">
                            Fallido
                          </span>
                        ) : (
                          <span className={`px-2 py-1 text-xs rounded ${schedule.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                            {schedule.is_active ? 'Activo' : 'Inactivo'}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(schedule.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setSelectedScheduleId(schedule.id)}
                            className="text-blue-600 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 px-3 py-1 rounded transition"
                            title="Ver detalles"
                          >
                            Ver
                          </button>
                          <button
                            onClick={() => handleExportExcel(schedule)}
                            disabled={exporting === schedule.id}
                            className="text-green-600 hover:text-green-900 bg-green-50 hover:bg-green-100 px-3 py-1 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Exportar a Excel"
                          >
                            {exporting === schedule.id ? '...' : 'Excel'}
                          </button>
                          <button
                            onClick={() => handleEditClick(schedule)}
                            className="text-indigo-600 hover:text-indigo-900 bg-indigo-50 hover:bg-indigo-100 px-3 py-1 rounded transition"
                            title="Editar nombre/descripción"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => handleDeleteClick(schedule)}
                            className="text-red-600 hover:text-red-900 bg-red-50 hover:bg-red-100 px-3 py-1 rounded transition"
                            title="Eliminar horario"
                          >
                            Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {paginatedData && (
              <Pagination
                currentPage={currentPage}
                totalPages={Math.ceil(paginatedData.count / 20)}
                onPageChange={setCurrentPage}
                totalItems={paginatedData.count}
              />
            )}
          </>
        )}
      </div>

      {/* Generate Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 transform transition-all scale-100">
            <div className="flex justify-between items-center mb-4 border-b pb-2">
              <h3 className="text-xl font-bold text-gray-900">Generar Nuevo Horario</h3>
              <button 
                onClick={() => setShowGenerateModal(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-light"
              >
                ×
              </button>
            </div>
            
            <form onSubmit={handleGenerate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                <input
                  type="text"
                  value={generateFormData.name}
                  onChange={(e) => setGenerateFormData({...generateFormData, name: e.target.value})}
                  placeholder="Ej: Horario 2025-1"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
                <textarea
                  value={generateFormData.description}
                  onChange={(e) => setGenerateFormData({...generateFormData, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4 bg-gray-50 p-3 rounded-md">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Población</label>
                  <input
                    type="number"
                    value={generateFormData.population_size}
                    onChange={(e) => setGenerateFormData({...generateFormData, population_size: parseInt(e.target.value)})}
                    min="10"
                    max="1000"
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Generaciones</label>
                  <input
                    type="number"
                    value={generateFormData.generations}
                    onChange={(e) => setGenerateFormData({...generateFormData, generations: parseInt(e.target.value)})}
                    min="10"
                    max="1000"
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded transition-colors"
                  disabled={generating}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-400 flex items-center gap-2 transition-colors shadow-sm"
                  disabled={generating}
                >
                  {generating ? (
                    <>
                      <span className="animate-spin">↻</span> Generando...
                    </>
                  ) : (
                    'Generar'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 transform transition-all scale-100">
            <div className="flex justify-between items-center mb-4 border-b pb-2">
              <h3 className="text-xl font-bold text-gray-900">Editar Horario</h3>
              <button 
                onClick={() => setShowEditModal(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-light"
              >
                ×
              </button>
            </div>
            
            <form onSubmit={handleUpdate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                <input
                  type="text"
                  value={editFormData.name}
                  onChange={(e) => setEditFormData({...editFormData, name: e.target.value})}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
                <textarea
                  value={editFormData.description}
                  onChange={(e) => setEditFormData({...editFormData, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                  rows={4}
                />
              </div>

              <div className="flex justify-end gap-3 mt-6 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded transition-colors"
                  disabled={processing}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-400 flex items-center gap-2 transition-colors shadow-sm"
                  disabled={processing}
                >
                  {processing ? (
                    <>
                      <span className="animate-spin">↻</span> Guardando...
                    </>
                  ) : (
                    'Guardar Cambios'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && scheduleToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-sm w-full p-6 transform transition-all scale-100">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <span className="text-red-600 text-xl">⚠️</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">¿Eliminar Horario?</h3>
              <p className="text-sm text-gray-500 mb-6">
                Estás a punto de eliminar el horario <span className="font-bold text-gray-700">"{scheduleToDelete.name}"</span>. 
                Esta acción no se puede deshacer.
              </p>
            </div>
            
            <div className="flex justify-center gap-3">
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded transition-colors"
                disabled={processing}
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-red-400 transition-colors shadow-sm"
                disabled={processing}
              >
                {processing ? 'Eliminando...' : 'Sí, Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Schedules;
