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
