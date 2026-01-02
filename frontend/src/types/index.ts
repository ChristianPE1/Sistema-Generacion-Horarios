export interface ImportStats {
  rooms: number;
  instructors: number;
  courses: number;
  classes: number;
  time_slots: number;
  students: number;
  enrollments: number;
}

export interface SavedSchedule {
  id: number;
  name: string;
  dataset: string;
  created_at: string;
  fitness_score: number;
  conflict_count: number;
  classes_assigned: number;
  classes_total: number;
  generation_time_ms: number;
  status: string;
}

export type ViewMode = 'room' | 'instructor' | 'year';

export interface ScheduleBlock {
  day: string;
  block: number;
  start: string;
  end: string;
}

export interface Assignment {
  class_id: string;
  class_name: string;
  class_type: string;
  year: number;
  room: { id: string; type: string };
  instructor: { id: string; name: string };
  schedule: ScheduleBlock[];
}

export interface SavedScheduleOption {
  id: number;
  name: string;
  dataset: string;
  created_at: string;
}

export interface RoomTypeConstraints {
  max_classes_per_day: number | null;
  max_classes_per_week: number | null;
  start_time: string;
  end_time: string;
}

export interface ScheduleConstraints {
  aulas: RoomTypeConstraints;
  laboratorios: RoomTypeConstraints;
  general: {
    max_consecutive_blocks: number;
    max_consecutive_lab_blocks: number;
    break_duration_minutes: number;
    block_duration_minutes: number;
  };
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}


// interfaz para datasets
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
  constraints_applied?: ScheduleConstraints;
  algorithm?: string;
  stats?: any;
}