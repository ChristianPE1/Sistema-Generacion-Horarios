import axios from 'axios';
import type {
  Room, Instructor, Course, Class, Student, Schedule,
  DashboardStats, CalendarEvent, ImportStats
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interfaz para respuestas paginadas
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Helper para obtener todos los resultados paginados
async function getAllPaginated<T>(url: string): Promise<T[]> {
  let allResults: T[] = [];
  let nextUrl: string | null = url;
  
  while (nextUrl) {
    const response = await api.get<PaginatedResponse<T>>(nextUrl);
    allResults = allResults.concat(response.data.results);
    nextUrl = response.data.next;
  }
  
  return allResults;
}

// Rooms
export const getRooms = (page?: number, pageSize?: number): Promise<{data: PaginatedResponse<Room>}> => {
  const params = new URLSearchParams();
  if (page) params.append('page', page.toString());
  if (pageSize) params.append('page_size', pageSize.toString());
  return api.get(`/rooms/?${params.toString()}`);
};

export const getAllRooms = (): Promise<{data: Room[]}> => 
  getAllPaginated<Room>('/rooms/').then(data => ({ data }));

export const getRoom = (id: number) => api.get<Room>(`/rooms/${id}/`);
export const createRoom = (data: Partial<Room>) => api.post<Room>('/rooms/', data);
export const updateRoom = (id: number, data: Partial<Room>) => api.put<Room>(`/rooms/${id}/`, data);
export const deleteRoom = (id: number) => api.delete(`/rooms/${id}/`);
export const getRoomsStatistics = () => api.get('/rooms/statistics/');

// Instructors
export const getInstructors = (page?: number, pageSize?: number): Promise<{data: PaginatedResponse<Instructor>}> => {
  const params = new URLSearchParams();
  if (page) params.append('page', page.toString());
  if (pageSize) params.append('page_size', pageSize.toString());
  return api.get(`/instructors/?${params.toString()}`);
};

export const getAllInstructors = (): Promise<{data: Instructor[]}> => 
  getAllPaginated<Instructor>('/instructors/').then(data => ({ data }));

export const getInstructor = (id: number) => api.get<Instructor>(`/instructors/${id}/`);
export const createInstructor = (data: Partial<Instructor>) => api.post<Instructor>('/instructors/', data);
export const updateInstructor = (id: number, data: Partial<Instructor>) => api.put<Instructor>(`/instructors/${id}/`, data);
export const deleteInstructor = (id: number) => api.delete(`/instructors/${id}/`);
export const getInstructorClasses = (id: number) => api.get(`/instructors/${id}/classes/`);
export const getInstructorsStatistics = () => api.get('/instructors/statistics/');

// Courses
export const getCourses = (page?: number, pageSize?: number): Promise<{data: PaginatedResponse<Course>}> => {
  const params = new URLSearchParams();
  if (page) params.append('page', page.toString());
  if (pageSize) params.append('page_size', pageSize.toString());
  return api.get(`/courses/?${params.toString()}`);
};

export const getAllCourses = (): Promise<{data: Course[]}> => 
  getAllPaginated<Course>('/courses/').then(data => ({ data }));

export const getCourse = (id: number) => api.get<Course>(`/courses/${id}/`);
export const createCourse = (data: Partial<Course>) => api.post<Course>('/courses/', data);
export const updateCourse = (id: number, data: Partial<Course>) => api.put<Course>(`/courses/${id}/`, data);
export const deleteCourse = (id: number) => api.delete(`/courses/${id}/`);
export const getCourseClasses = (id: number) => api.get(`/courses/${id}/classes/`);

// Classes
export const getClasses = (page?: number, pageSize?: number): Promise<{data: PaginatedResponse<Class>}> => {
  const params = new URLSearchParams();
  if (page) params.append('page', page.toString());
  if (pageSize) params.append('page_size', pageSize.toString());
  return api.get(`/classes/?${params.toString()}`);
};

export const getAllClasses = (): Promise<{data: Class[]}> => 
  getAllPaginated<Class>('/classes/').then(data => ({ data }));

export const getClass = (id: number) => api.get<Class>(`/classes/${id}/`);
export const createClass = (data: Partial<Class>) => api.post<Class>('/classes/', data);
export const updateClass = (id: number, data: Partial<Class>) => api.put<Class>(`/classes/${id}/`, data);
export const deleteClass = (id: number) => api.delete(`/classes/${id}/`);
export const getClassStudents = (id: number) => api.get(`/classes/${id}/students/`);
export const getClassesStatistics = () => api.get('/classes/statistics/');

// Students
export const getStudents = (page?: number, pageSize?: number): Promise<{data: PaginatedResponse<Student>}> => {
  const params = new URLSearchParams();
  if (page) params.append('page', page.toString());
  if (pageSize) params.append('page_size', pageSize.toString());
  return api.get(`/students/?${params.toString()}`);
};

export const getAllStudents = (): Promise<{data: Student[]}> => 
  getAllPaginated<Student>('/students/').then(data => ({ data }));

export const getStudent = (id: number) => api.get<Student>(`/students/${id}/`);
export const createStudent = (data: Partial<Student>) => api.post<Student>('/students/', data);
export const updateStudent = (id: number, data: Partial<Student>) => api.put<Student>(`/students/${id}/`, data);
export const deleteStudent = (id: number) => api.delete(`/students/${id}/`);
export const getStudentClasses = (id: number) => api.get(`/students/${id}/classes/`);

// Schedules
export const getSchedules = (page?: number, pageSize?: number): Promise<{data: PaginatedResponse<Schedule>}> => {
  const params = new URLSearchParams();
  if (page) params.append('page', page.toString());
  if (pageSize) params.append('page_size', pageSize.toString());
  return api.get(`/schedules/?${params.toString()}`);
};

export const getAllSchedules = (): Promise<{data: Schedule[]}> => 
  getAllPaginated<Schedule>('/schedules/').then(data => ({ data }));

export const getSchedule = (id: number) => api.get<Schedule>(`/schedules/${id}/`);
export const createSchedule = (data: Partial<Schedule>) => api.post<Schedule>('/schedules/', data);
export const updateSchedule = (id: number, data: Partial<Schedule>) => api.put<Schedule>(`/schedules/${id}/`, data);
export const deleteSchedule = (id: number) => api.delete(`/schedules/${id}/`);
export const activateSchedule = (id: number) => api.post(`/schedules/${id}/activate/`);
export const getScheduleCalendarView = (id: number) => api.get<CalendarEvent[]>(`/schedules/${id}/calendar_view/`);
export const getScheduleTimetable = (id: number) => api.get(`/schedules/${id}/timetable/`);

// LEGACY - Generación con BD (lento)
export const generateSchedule = (data: {
  name: string;
  description?: string;
  population_size?: number;
  generations?: number;
  mutation_rate?: number;
  crossover_rate?: number;
}) => api.post('/schedules/generate/', data);

// =====================================================
// NUEVO: Generación con Algoritmo Genético Optimizado
// =====================================================

// Interfaz para datasets disponibles
export interface DatasetInfo {
  name: string;
  path: string;
  type: 'xml' | 'json';
  stats?: {
    rooms: number;
    instructors: number;
    classes?: number;
    courses?: number;
  };
  error?: string;
}

// Interfaz para horario generado
export interface GeneratedSchedule {
  name?: string;
  dataset?: string;
  assignments: Array<{
    class_id: string;
    class_name: string;
    class_type: string;
    year: number;
    room: {
      id: string;
      type: string;
    };
    instructor: {
      id: string;
      name: string;
    };
    schedule: Array<{
      day: string;
      block: number;
      start: string;
      end: string;
    }>;
  }>;
  fitness_score: number;
  conflict_count: number;
  generation_time_ms: number;
  generations_run: number;
  classes_assigned: number;
  classes_total: number;
  unassigned: string[];
}

// Lista datasets disponibles (escuela.xml, purdue_clean.xml)
export const getDatasets = () => 
  api.get<{success: boolean; datasets: DatasetInfo[]}>('/generate/datasets/');

// Preparar datasets (limpiar XML Purdue, convertir JSON escuela)
export const prepareDatasets = () => 
  api.post<{success: boolean; results: any}>('/generate/prepare/');

// Generar horario desde dataset
export const generateScheduleFromDataset = (data: {
  dataset: string;
  name: string;
  population_size?: number;
  generations?: number;
}) => api.post<{success: boolean; schedule: GeneratedSchedule}>('/generate/schedule/', data);

// Generar horario desde archivo subido
export const generateScheduleFromUpload = (formData: FormData) => {
  return axios.post<{success: boolean; schedule: GeneratedSchedule}>(`${API_BASE_URL}/generate/upload/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// Obtener último horario generado
export const getLastGeneratedSchedule = () => 
  api.get<{success: boolean; schedule: GeneratedSchedule}>('/generate/last/');

// Import XML
export const importXML = (formData: FormData) => {
  return axios.post<{success: boolean; message: string; stats: ImportStats}>(`${API_BASE_URL}/import-xml/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// Dashboard Stats
export const getDashboardStats = () => api.get<DashboardStats>('/dashboard-stats/');

export default api;
