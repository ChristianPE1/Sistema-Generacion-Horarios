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

// Rooms
export const getRooms = () => api.get<Room[]>('/rooms/');
export const getRoom = (id: number) => api.get<Room>(`/rooms/${id}/`);
export const createRoom = (data: Partial<Room>) => api.post<Room>('/rooms/', data);
export const updateRoom = (id: number, data: Partial<Room>) => api.put<Room>(`/rooms/${id}/`, data);
export const deleteRoom = (id: number) => api.delete(`/rooms/${id}/`);
export const getRoomsStatistics = () => api.get('/rooms/statistics/');

// Instructors
export const getInstructors = () => api.get<Instructor[]>('/instructors/');
export const getInstructor = (id: number) => api.get<Instructor>(`/instructors/${id}/`);
export const createInstructor = (data: Partial<Instructor>) => api.post<Instructor>('/instructors/', data);
export const updateInstructor = (id: number, data: Partial<Instructor>) => api.put<Instructor>(`/instructors/${id}/`, data);
export const deleteInstructor = (id: number) => api.delete(`/instructors/${id}/`);
export const getInstructorClasses = (id: number) => api.get(`/instructors/${id}/classes/`);
export const getInstructorsStatistics = () => api.get('/instructors/statistics/');

// Courses
export const getCourses = () => api.get<Course[]>('/courses/');
export const getCourse = (id: number) => api.get<Course>(`/courses/${id}/`);
export const createCourse = (data: Partial<Course>) => api.post<Course>('/courses/', data);
export const updateCourse = (id: number, data: Partial<Course>) => api.put<Course>(`/courses/${id}/`, data);
export const deleteCourse = (id: number) => api.delete(`/courses/${id}/`);
export const getCourseClasses = (id: number) => api.get(`/courses/${id}/classes/`);

// Classes
export const getClasses = () => api.get<Class[]>('/classes/');
export const getClass = (id: number) => api.get<Class>(`/classes/${id}/`);
export const createClass = (data: Partial<Class>) => api.post<Class>('/classes/', data);
export const updateClass = (id: number, data: Partial<Class>) => api.put<Class>(`/classes/${id}/`, data);
export const deleteClass = (id: number) => api.delete(`/classes/${id}/`);
export const getClassStudents = (id: number) => api.get(`/classes/${id}/students/`);
export const getClassesStatistics = () => api.get('/classes/statistics/');

// Students
export const getStudents = () => api.get<Student[]>('/students/');
export const getStudent = (id: number) => api.get<Student>(`/students/${id}/`);
export const createStudent = (data: Partial<Student>) => api.post<Student>('/students/', data);
export const updateStudent = (id: number, data: Partial<Student>) => api.put<Student>(`/students/${id}/`, data);
export const deleteStudent = (id: number) => api.delete(`/students/${id}/`);
export const getStudentClasses = (id: number) => api.get(`/students/${id}/classes/`);

// Schedules
export const getSchedules = () => api.get<Schedule[]>('/schedules/');
export const getSchedule = (id: number) => api.get<Schedule>(`/schedules/${id}/`);
export const createSchedule = (data: Partial<Schedule>) => api.post<Schedule>('/schedules/', data);
export const updateSchedule = (id: number, data: Partial<Schedule>) => api.put<Schedule>(`/schedules/${id}/`, data);
export const deleteSchedule = (id: number) => api.delete(`/schedules/${id}/`);
export const activateSchedule = (id: number) => api.post(`/schedules/${id}/activate/`);
export const getScheduleCalendarView = (id: number) => api.get<CalendarEvent[]>(`/schedules/${id}/calendar_view/`);

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
