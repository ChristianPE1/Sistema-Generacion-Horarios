import React, { useState, useEffect } from 'react'
import FullCalendar from '@fullcalendar/react'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import api from '../services/api'

interface Room {
  id: number
  xml_id: string
  building?: string
  capacity: number
}

interface Schedule {
  id: number
  name: string
  description: string
  fitness_score: number
  created_at: string
}

interface ClassAssignment {
  id: number
  class_id: number  // xml_id de la clase
  class_name: string
  room_id: string  // xml_id del aula
  instructor_name: string
  days: string // "0110000" formato binario
  start_time: number // minutos desde medianoche
  length: number // duración en minutos
  student_count: number
  has_conflict: boolean
}

interface ScheduleViewerProps {
  scheduleId?: number
}

const ScheduleViewer: React.FC<ScheduleViewerProps> = ({ scheduleId: initialScheduleId }) => {
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [selectedScheduleId, setSelectedScheduleId] = useState<number | null>(initialScheduleId || null)
  const [rooms, setRooms] = useState<Room[]>([])
  const [currentRoomIndex, setCurrentRoomIndex] = useState(0)
  const [assignments, setAssignments] = useState<ClassAssignment[]>([])
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [conflictCount, setConflictCount] = useState(0)

  useEffect(() => {
    loadSchedules()
    loadRooms()
  }, [])

  useEffect(() => {
    if (rooms.length > 0 && selectedScheduleId) {
      loadAssignments(rooms[currentRoomIndex].id)
    }
  }, [currentRoomIndex, rooms, selectedScheduleId])

  const loadSchedules = async () => {
    try {
      const response = await api.get('/schedules/')
      // La API retorna datos paginados con "results"
      const schedulesData = response.data.results || response.data
      console.log('Schedules cargados:', schedulesData.length)
      setSchedules(schedulesData)
      // Si no hay schedule seleccionado, tomar el más reciente
      if (!selectedScheduleId && schedulesData.length > 0) {
        setSelectedScheduleId(schedulesData[0].id)
        console.log('Schedule seleccionado:', schedulesData[0].id, schedulesData[0].name)
      }
    } catch (error) {
      console.error('Error cargando schedules:', error)
    }
  }

  const loadRooms = async () => {
    try {
      // Cargar todas las aulas (sin paginación)
      const response = await api.get('/rooms/?page_size=1000')
      // La API retorna datos paginados con "results"
      const roomsData = response.data.results || response.data
      console.log('Aulas cargadas:', roomsData.length)
      setRooms(roomsData)
      setLoading(false)
    } catch (error) {
      console.error('Error cargando aulas:', error)
      setLoading(false)
    }
  }

  const loadAssignments = async (roomId: number) => {
    if (!selectedScheduleId) return
    
    try {
      setLoading(true)
      const endpoint = `/schedules/${selectedScheduleId}/room/${roomId}/assignments/`
      console.log('Cargando asignaciones desde:', endpoint)
      const response = await api.get(endpoint)
      const assignmentsData = response.data

      console.log('Asignaciones recibidas:', assignmentsData.length)
      setAssignments(assignmentsData)

      // Convertir asignaciones a eventos de FullCalendar
      const calendarEvents = convertToCalendarEvents(assignmentsData)
      console.log('Eventos del calendario:', calendarEvents.length)
      setEvents(calendarEvents)

      // Contar conflictos
      const conflicts = assignmentsData.filter((a: ClassAssignment) => a.has_conflict).length
      setConflictCount(conflicts)

      setLoading(false)
    } catch (error) {
      console.error('Error cargando asignaciones:', error)
      setLoading(false)
    }
  }

  const convertToCalendarEvents = (assignments: ClassAssignment[]) => {
    const events: any[] = []

    assignments.forEach(assignment => {
      // Decodificar días de la semana (formato binario "0110000")
      const days = assignment.days

      days.split('').forEach((bit, index) => {
        if (bit === '1') {
          // Crear evento para cada día
          const daysOfWeek = [index] // 0=Domingo, 1=Lunes, etc.

          // Convertir start_time (minutos) a hora "HH:mm"
          const startHour = Math.floor(assignment.start_time / 60)
          const startMin = assignment.start_time % 60
          const endTime = assignment.start_time + assignment.length
          const endHour = Math.floor(endTime / 60)
          const endMin = endTime % 60

          events.push({
            id: `${assignment.id}-${index}`,
            title: `Clase ${assignment.class_id}`,
            daysOfWeek,
            startTime: `${startHour.toString().padStart(2, '0')}:${startMin.toString().padStart(2, '0')}`,
            endTime: `${endHour.toString().padStart(2, '0')}:${endMin.toString().padStart(2, '0')}`,
            backgroundColor: assignment.has_conflict ? '#ef4444' : '#3b82f6',
            borderColor: assignment.has_conflict ? '#dc2626' : '#2563eb',
            textColor: '#ffffff',
            extendedProps: {
              classXmlId: assignment.class_id,
              courseName: assignment.class_name,
              instructor: assignment.instructor_name,
              students: assignment.student_count,
              conflict: assignment.has_conflict
            }
          })
        }
      })
    })

    return events
  }

  const handlePrevRoom = () => {
    if (currentRoomIndex > 0) {
      setCurrentRoomIndex(currentRoomIndex - 1)
    }
  }

  const handleNextRoom = () => {
    if (currentRoomIndex < rooms.length - 1) {
      setCurrentRoomIndex(currentRoomIndex + 1)
    }
  }

  const handleEventClick = (info: any) => {
    const props = info.event.extendedProps
    alert(
      `Clase XML ID: ${props.classXmlId}\n` +
      `Curso: ${props.courseName}\n` +
      `Instructor: ${props.instructor}\n` +
      `Estudiantes: ${props.students}\n` +
      `Conflicto: ${props.conflict ? 'SÍ' : 'No'}`
    )
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Cargando horarios...</div>
      </div>
    )
  }

  if (schedules.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">No hay horarios disponibles</div>
      </div>
    )
  }

  if (rooms.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">No hay aulas disponibles</div>
      </div>
    )
  }

  if (!selectedScheduleId) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Seleccione un horario</div>
      </div>
    )
  }

  const currentRoom = rooms[currentRoomIndex]
  const currentSchedule = schedules.find(s => s.id === selectedScheduleId)

  if (!currentRoom) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">No se encontró el aula actual</div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Selector de Schedule */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Seleccionar Horario
        </label>
        <select
          value={selectedScheduleId || ''}
          onChange={(e) => setSelectedScheduleId(Number(e.target.value))}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {schedules.map((schedule) => (
            <option key={schedule.id} value={schedule.id}>
              {schedule.name} (Fitness: {schedule.fitness_score?.toFixed(0) || 'N/A'})
            </option>
          ))}
        </select>
        {currentSchedule && (
          <div className="mt-2 text-sm text-gray-600">
            {currentSchedule.description && <p>{currentSchedule.description}</p>}
            <p>Creado: {new Date(currentSchedule.created_at).toLocaleString('es-ES')}</p>
          </div>
        )}
      </div>

      {/* Header con navegación */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">
              Horario del Aula
            </h2>
            <p className="text-gray-600">
              Vista {currentRoomIndex + 1} de {rooms.length}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handlePrevRoom}
              disabled={currentRoomIndex === 0}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              ← Anterior
            </button>
            <button
              onClick={handleNextRoom}
              disabled={currentRoomIndex === rooms.length - 1}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Siguiente →
            </button>
          </div>
        </div>

        {/* Info del aula actual */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-gray-600">Aula</div>
            <div className="text-xl font-bold text-blue-600">
              {currentRoom?.xml_id || 'N/A'}
            </div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-sm text-gray-600">Capacidad</div>
            <div className="text-xl font-bold text-green-600">
              {currentRoom?.capacity || 0}
            </div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-sm text-gray-600">Clases Asignadas</div>
            <div className="text-xl font-bold text-purple-600">
              {assignments.length}
            </div>
          </div>
          <div className={`${conflictCount > 0 ? 'bg-red-50' : 'bg-gray-50'} p-3 rounded`}>
            <div className="text-sm text-gray-600">Conflictos</div>
            <div className={`text-xl font-bold ${conflictCount > 0 ? 'text-red-600' : 'text-gray-600'}`}>
              {conflictCount}
            </div>
          </div>
        </div>

        {conflictCount > 0 && (
          <div className="mt-4 p-3 bg-red-100 border border-red-300 rounded text-red-800">
            ⚠️ Esta aula tiene {conflictCount} conflicto(s) de horario
          </div>
        )}
      </div>

      {/* Calendario */}
      <div className="bg-white rounded-lg shadow p-4">
        <FullCalendar
          plugins={[timeGridPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          headerToolbar={{
            left: '',
            center: 'title',
            right: ''
          }}
          titleFormat={{ year: 'numeric', month: 'long', day: 'numeric' }}
          slotMinTime="07:00:00"
          slotMaxTime="22:00:00"
          allDaySlot={false}
          height="auto"
          events={events}
          eventClick={handleEventClick}
          eventTimeFormat={{
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          }}
          slotLabelFormat={{
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          }}
          locale="es"
          weekends={true}
          slotDuration="00:30:00"
          slotLabelInterval="01:00"
          dayHeaderFormat={{ weekday: 'long' }}
          initialDate="2007-01-01"
          validRange={{
            start: '2007-01-01',
            end: '2007-01-08'
          }}
          firstDay={1}
          eventContent={(arg) => {
            const props = arg.event.extendedProps
            return (
              <div className="p-1 overflow-hidden text-xs w-full h-full">
                <div className="font-semibold truncate">{arg.event.title}</div>
                <div className="truncate text-[10px]">{props.instructor}</div>
              </div>
            )
          }}
        />
      </div>

      {/* Leyenda */}
      <div className="mt-4 bg-white rounded-lg shadow p-4">
        <h3 className="font-bold mb-2">Leyenda:</h3>
        <div className="flex gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span className="text-sm">Sin conflictos</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span className="text-sm">Con conflictos</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ScheduleViewer
