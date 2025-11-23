import React, { useState, useEffect, useMemo } from 'react'
import FullCalendar from '@fullcalendar/react'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { getAllRooms, getAllSchedules, getAllInstructors, getScheduleCalendarView } from '../services/api'
import type { CalendarEvent, Room, Instructor, Schedule } from '../types'

interface ScheduleViewerProps {
  scheduleId?: number
}

type ViewMode = 'room' | 'instructor'

const ScheduleViewer: React.FC<ScheduleViewerProps> = ({ scheduleId: initialScheduleId }) => {
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [selectedScheduleId, setSelectedScheduleId] = useState<number | null>(initialScheduleId || null)
  
  // Data
  const [rooms, setRooms] = useState<Room[]>([])
  const [instructors, setInstructors] = useState<Instructor[]>([])
  const [allEvents, setAllEvents] = useState<CalendarEvent[]>([])
  
  // View State
  const [viewMode, setViewMode] = useState<ViewMode>('room')
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null)
  const [selectedInstructorName, setSelectedInstructorName] = useState<string | null>(null)
  
  const [loading, setLoading] = useState(true)
  const [loadingEvents, setLoadingEvents] = useState(false)

  useEffect(() => {
    const init = async () => {
      setLoading(true)
      await Promise.all([loadSchedules(), loadRooms(), loadInstructors()])
      setLoading(false)
    }
    init()
  }, [])

  useEffect(() => {
    if (selectedScheduleId) {
      loadScheduleEvents(selectedScheduleId)
    }
  }, [selectedScheduleId])

  // Set default selections when data loads
  useEffect(() => {
    if (rooms.length > 0 && !selectedRoomId) {
      setSelectedRoomId(rooms[0].id)
    }
  }, [rooms])

  useEffect(() => {
    if (instructors.length > 0 && !selectedInstructorName) {
      // Find first instructor with events if possible, otherwise just the first one
      setSelectedInstructorName(instructors[0].name || `Instructor ${instructors[0].xml_id}`)
    }
  }, [instructors])

  const loadSchedules = async () => {
    try {
      const response = await getAllSchedules()
      setSchedules(response.data)
      if (!selectedScheduleId && response.data.length > 0) {
        setSelectedScheduleId(response.data[0].id)
      }
    } catch (error) {
      console.error('Error cargando schedules:', error)
    }
  }

  const loadRooms = async () => {
    try {
      const response = await getAllRooms()
      setRooms(response.data.sort((a, b) => a.xml_id - b.xml_id))
    } catch (error) {
      console.error('Error cargando aulas:', error)
    }
  }

  const loadInstructors = async () => {
    try {
      const response = await getAllInstructors()
      setInstructors(response.data.sort((a, b) => a.name.localeCompare(b.name)))
    } catch (error) {
      console.error('Error cargando instructores:', error)
    }
  }

  const loadScheduleEvents = async (scheduleId: number) => {
    try {
      setLoadingEvents(true)
      const response = await getScheduleCalendarView(scheduleId)
      setAllEvents(response.data)
    } catch (error) {
      console.error('Error cargando eventos:', error)
    } finally {
      setLoadingEvents(false)
    }
  }

  // Filter events based on current view and selection
  const filteredEvents = useMemo(() => {
    if (!allEvents.length) return []

    if (viewMode === 'room') {
      if (!selectedRoomId) return []
      // Filter by roomId (using the new prop added to backend) or fallback to string matching
      return allEvents.filter(event => {
        if (event.extendedProps.roomId) {
          return event.extendedProps.roomId === selectedRoomId
        }
        // Fallback for older backend responses
        const room = rooms.find(r => r.id === selectedRoomId)
        return room && event.extendedProps.room === `Room ${room.xml_id}`
      })
    } else {
      if (!selectedInstructorName) return []
      return allEvents.filter(event => {
        const eventInstructors = event.extendedProps.instructors
        if (Array.isArray(eventInstructors)) {
          return eventInstructors.includes(selectedInstructorName)
        }
        return false
      })
    }
  }, [allEvents, viewMode, selectedRoomId, selectedInstructorName, rooms])

  // Calculate stats for current view
  const stats = useMemo(() => {
    const conflictCount = filteredEvents.filter(e => e.extendedProps.conflict).length
    const totalClasses = filteredEvents.length
    const totalHours = filteredEvents.reduce((acc, curr) => {
      const start = new Date(`2000-01-01T${curr.startTime}`).getTime()
      const end = new Date(`2000-01-01T${curr.endTime}`).getTime()
      return acc + (end - start) / (1000 * 60 * 60)
    }, 0)

    return { conflictCount, totalClasses, totalHours }
  }, [filteredEvents])

  const handleEventClick = (info: any) => {
    const props = info.event.extendedProps
    alert(
      `Clase: ${info.event.title}\n` +
      `Aula: ${props.room}\n` +
      `Instructor: ${props.instructors.join(', ')}\n` +
      `Estudiantes: ${props.students}\n` +
      `Conflicto: ${props.conflict ? 'SÍ' : 'No'}`
    )
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const currentSchedule = schedules.find(s => s.id === selectedScheduleId)

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header & Controls */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Visualizador de Horarios</h2>
            <p className="text-gray-500 text-sm mt-1">
              {currentSchedule ? (
                <>
                  <span className="font-medium text-gray-900">{currentSchedule.name}</span>
                  <span className="mx-2">•</span>
                  Fitness: <span className="text-green-600 font-mono">{currentSchedule.fitness_score.toLocaleString()}</span>
                </>
              ) : 'Seleccione un horario'}
            </p>
          </div>
          
          <div className="flex items-center gap-3 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setViewMode('room')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                viewMode === 'room' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Por Aula
            </button>
            <button
              onClick={() => setViewMode('instructor')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                viewMode === 'instructor' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Por Instructor
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Horario</label>
            <select
              value={selectedScheduleId || ''}
              onChange={(e) => setSelectedScheduleId(Number(e.target.value))}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            >
              {schedules.map((schedule) => (
                <option key={schedule.id} value={schedule.id}>
                  {schedule.name}
                </option>
              ))}
            </select>
          </div>

          {viewMode === 'room' ? (
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Aula</label>
              <select
                value={selectedRoomId || ''}
                onChange={(e) => setSelectedRoomId(Number(e.target.value))}
                className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
              >
                {rooms.map((room) => (
                  <option key={room.id} value={room.id}>
                    Aula {room.xml_id} (Cap: {room.capacity})
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Instructor</label>
              <select
                value={selectedInstructorName || ''}
                onChange={(e) => setSelectedInstructorName(e.target.value)}
                className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
              >
                {instructors.map((instructor) => (
                  <option key={instructor.id} value={instructor.name || `Instructor ${instructor.xml_id}`}>
                    {instructor.name || `Instructor ${instructor.xml_id}`}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex items-end">
            <div className="w-full bg-blue-50 rounded-lg p-2 flex justify-around items-center border border-blue-100">
              <div className="text-center">
                <div className="text-xs text-blue-600 font-medium">Clases</div>
                <div className="text-lg font-bold text-blue-800">{stats.totalClasses}</div>
              </div>
              <div className="w-px h-8 bg-blue-200"></div>
              <div className="text-center">
                <div className="text-xs text-blue-600 font-medium">Horas</div>
                <div className="text-lg font-bold text-blue-800">{stats.totalHours.toFixed(1)}</div>
              </div>
              <div className="w-px h-8 bg-blue-200"></div>
              <div className="text-center">
                <div className="text-xs text-red-600 font-medium">Conflictos</div>
                <div className={`text-lg font-bold ${stats.conflictCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {stats.conflictCount}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Calendar Area */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1 relative min-h-[600px]">
        {loadingEvents && (
          <div className="absolute inset-0 bg-white/80 z-10 flex items-center justify-center backdrop-blur-sm rounded-xl">
            <div className="flex flex-col items-center gap-3">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
              <span className="text-gray-500 font-medium">Cargando eventos...</span>
            </div>
          </div>
        )}
        
        <FullCalendar
          plugins={[timeGridPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          headerToolbar={{
            left: '',
            center: '',
            right: ''
          }}
          allDaySlot={false}
          slotMinTime="07:00:00"
          slotMaxTime="22:00:00"
          height="auto"
          events={filteredEvents}
          eventClick={handleEventClick}
          locale="es"
          weekends={true}
          slotDuration="00:30:00"
          dayHeaderFormat={{ weekday: 'long' }}
          initialDate="2007-01-01"
          firstDay={1}
          eventContent={(arg) => {
            const props = arg.event.extendedProps
            return (
              <div className="h-full w-full p-1 flex flex-col overflow-hidden">
                <div className="font-bold text-xs truncate leading-tight">{arg.event.title}</div>
                <div className="text-[10px] opacity-90 truncate mt-0.5">
                  {viewMode === 'room' ? props.instructors.join(', ') : props.room}
                </div>
                {props.conflict && (
                  <div className="absolute top-1 right-1 text-[10px]">⚠️</div>
                )}
              </div>
            )
          }}
        />
      </div>
    </div>
  )
}

export default ScheduleViewer
