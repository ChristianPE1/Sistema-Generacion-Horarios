import axios from 'axios';
import type { ImportStats } from '../types';

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

// Preparar datasets
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

// Listar horarios guardados en BD
export const getSavedSchedules = () => 
  api.get<{success: boolean; schedules: Array<{
    id: number;
    name: string;
    dataset: string;
    fitness_score: number;
    conflict_count: number;
    classes_assigned: number;
    classes_total: number;
    generation_time_ms: number;
    created_at: string;
    status: string;
  }>}>('/generate/saved/');

// Obtener horario específico por ID
export const getSavedSchedule = (id: number) => 
  api.get<{success: boolean; schedule: GeneratedSchedule}>(`/generate/saved/${id}/`);

// Import XML
export const importXML = (formData: FormData) => {
  return axios.post<{success: boolean; message: string; stats: ImportStats}>(`${API_BASE_URL}/import-xml/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};


export default api;
