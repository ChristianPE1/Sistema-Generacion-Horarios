// Types para el sistema de horarios

export interface Room {
  id: number;
  xml_id: number;
  capacity: number;
  location: string;
  is_constraint: boolean;
}

export interface Instructor {
  id: number;
  xml_id: number;
  name: string;
  email?: string;
  class_count?: number;
}

export interface Course {
  id: number;
  xml_id: number;
  name: string;
  code: string;
  class_count?: number;
}

export interface TimeSlot {
  id: number;
  class_obj: number;
  days: string;
  start_time: number;
  length: number;
  preference: number;
  day_names?: string[];
  start_time_formatted?: string;
  end_time_formatted?: string;
}

export interface ClassInstructor {
  id: number;
  class_obj: number;
  instructor: number;
  instructor_name?: string;
}

export interface ClassRoom {
  id: number;
  class_obj: number;
  room: number;
  preference: number;
  room_capacity?: number;
}

export interface Class {
  id: number;
  xml_id: number;
  offering?: number;
  offering_name?: string;
  config?: number;
  subpart?: number;
  class_limit: number;
  committed: boolean;
  scheduler?: number;
  dates: string;
  parent?: number;
  instructors?: ClassInstructor[];
  instructor_names?: string[];
  room_prefs?: ClassRoom[];
  room_names?: string[];
  time_slots?: TimeSlot[];
  student_count?: number;
}

export interface Student {
  id: number;
  xml_id: number;
  name: string;
  email?: string;
  enrolled_classes_count?: number;
}

export interface StudentClass {
  id: number;
  student: number;
  class_obj: number;
  student_name?: string;
  class_info?: string;
}

export interface Schedule {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  fitness_score: number;
  is_active: boolean;
  assignment_count?: number;
}

export interface ScheduleAssignment {
  id: number;
  schedule: number;
  class_obj: number;
  room: number;
  time_slot: number;
}

export interface CalendarEvent {
  id: string;
  title: string;
  daysOfWeek: number[];
  startTime: string;
  endTime: string;
  extendedProps: {
    classId: number;
    room: string;
    roomCapacity: number;
    instructors: string[];
    classLimit: number;
  };
}

export interface DashboardStats {
  rooms: {
    total: number;
    avg_capacity: number;
    with_constraints: number;
  };
  instructors: {
    total: number;
    with_classes: number;
  };
  courses: {
    total: number;
    with_classes: number;
  };
  classes: {
    total: number;
    committed: number;
    with_instructor: number;
    avg_limit: number;
  };
  students: {
    total: number;
    enrolled: number;
  };
  timeslots: {
    total: number;
  };
}

export interface ImportStats {
  rooms: number;
  instructors: number;
  courses: number;
  classes: number;
  time_slots: number;
  students: number;
  enrollments: number;
}
