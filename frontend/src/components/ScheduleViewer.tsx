import React, { useState, useEffect } from 'react'
import FullCalendar from '@fullcalendar/react'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import api from '../services/api'

interface Room {
  id: number
  room_id: string
  building?: string
  capacity: number
}

interface ClassAssignment {
  id: number
  class_id: number
  class_name: string
  room_id: number
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

const ScheduleViewer: React.FC<ScheduleViewerProps> = ({ scheduleId }) => {
  const [rooms, setRooms] = useState<Room[]>([])
  const [currentRoomIndex, setCurrentRoomIndex] = useState(0)
  const [assignments, setAssignments] = useState<ClassAssignment[]>([])
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [conflictCount, setConflictCount] = useState(0)

  useEffect(() => {
    loadRooms()
  }, [])

  useEffect(() => {
    if (rooms.length > 0) {
      loadAssignments(rooms[currentRoomIndex].id)
    }
  }, [currentRoomIndex, rooms])

  const loadRooms = async () => {
    try {
      const response = await api.get('/rooms/')
      setRooms(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error cargando aulas:', error)
      setLoading(false)
    }
  }

  const loadAssignments = async (roomId: number) => {
    try {
      setLoading(true)
      const endpoint = scheduleId
        ? `/schedules/${scheduleId}/room/${roomId}/assignments/`
        : `/rooms/${roomId}/assignments/`

      const response = await api.get(endpoint)
      const assignmentsData = response.data

      setAssignments(assignmentsData)

      // Convertir asignaciones a eventos de FullCalendar
      const calendarEvents = convertToCalendarEvents(assignmentsData)
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
            title: `${assignment.class_name}\n${assignment.instructor_name}`,
            daysOfWeek,
            startTime: `${startHour.toString().padStart(2, '0')}:${startMin.toString().padStart(2, '0')}`,
            endTime: `${endHour.toString().padStart(2, '0')}:${endMin.toString().padStart(2, '0')}`,
            backgroundColor: assignment.has_conflict ? '#ef4444' : '#3b82f6',
            borderColor: assignment.has_conflict ? '#dc2626' : '#2563eb',
            extendedProps: {
              classId: assignment.class_id,
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
      `Clase: ${info.event.title}\n` +
      `Instructor: ${props.instructor}\n` +
      `Estudiantes: ${props.students}\n` +
      `Conflicto: ${props.conflict ? 'SÍ ⚠️' : 'No'}`
    )
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Cargando horarios...</div>
      </div>
    )
  }

  const currentRoom = rooms[currentRoomIndex]

  return (
    <div className="max-w-7xl mx-auto p-6">
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
              {currentRoom?.room_id || 'N/A'}
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
            center: 'Horario Semanal del Aula',
            right: ''
          }}
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
          locale="es"
          weekends={false}
          slotDuration="00:30:00"
          slotLabelInterval="01:00"
          dayHeaderFormat={{ weekday: 'long' }}
          initialDate="2007-01-01"
          validRange={{
            start: '2007-01-01',
            end: '2007-01-07'
          }}
          eventContent={(arg) => {
            return (
              <div className="p-1 overflow-hidden text-xs">
                <div className="font-semibold truncate">{arg.event.title.split('\n')[0]}</div>
                <div className="truncate">{arg.event.extendedProps.instructor}</div>
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
