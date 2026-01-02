import axios, { type AxiosResponse } from 'axios';
import type { ImportStats, ScheduleConstraints, DatasetInfo, GeneratedSchedule } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getConstraints = (): Promise<AxiosResponse<{success: boolean; constraints: ScheduleConstraints}>> => 
  api.get('/generate/constraints/');

export const deleteSchedule = (id: number): Promise<AxiosResponse<{success: boolean; message: string}>> => 
  api.delete(`/generate/saved/${id}/delete/`);


// Lista datasets disponibles (escuela.xml, purdue_clean.xml)
export const getDatasets = (): Promise<AxiosResponse<{success: boolean; datasets: DatasetInfo[]}>> => 
  api.get('/generate/datasets/');

// Preparar datasets
export const prepareDatasets = (): Promise<AxiosResponse<{success: boolean; results: any}>> => 
  api.post('/generate/prepare/');


// Generar horario desde dataset (con constraints opcionales)
export const generateScheduleFromDataset = (data: {
  dataset: string;
  name: string;
  population_size?: number;
  generations?: number;
  constraints?: Partial<ScheduleConstraints>;
}): Promise<AxiosResponse<{success: boolean; schedule: GeneratedSchedule}>> => 
  api.post('/generate/schedule/', data);

// Generar horario desde archivo subido
export const generateScheduleFromUpload = (formData: FormData): Promise<AxiosResponse<{success: boolean; schedule: GeneratedSchedule}>> => {
  return axios.post(`${API_BASE_URL}/generate/upload/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// Obtener último horario generado
export const getLastGeneratedSchedule = (): Promise<AxiosResponse<{success: boolean; schedule: GeneratedSchedule}>> => 
  api.get('/generate/last/');

// Listar horarios guardados en BD
export const getSavedSchedules = (): Promise<AxiosResponse<{success: boolean; schedules: Array<{
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
}>}>> => api.get('/generate/saved/');

// Obtener horario específico por ID
export const getSavedSchedule = (id: number): Promise<AxiosResponse<{success: boolean; schedule: GeneratedSchedule}>> => 
  api.get(`/generate/saved/${id}/`);

// Import XML
export const importXML = (formData: FormData): Promise<AxiosResponse<{success: boolean; message: string; stats: ImportStats}>> => {
  return axios.post(`${API_BASE_URL}/import-xml/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};


export default api;
