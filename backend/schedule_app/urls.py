from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomViewSet, InstructorViewSet, CourseViewSet,
    ClassViewSet, StudentViewSet, ScheduleViewSet,
    TimeSlotViewSet, ClassInstructorViewSet, ClassRoomViewSet
)
from . import xml_parser
from . import api

router = DefaultRouter()
router.register(r'rooms', RoomViewSet)
router.register(r'instructors', InstructorViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'classes', ClassViewSet)
router.register(r'students', StudentViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'timeslots', TimeSlotViewSet)
router.register(r'class-instructors', ClassInstructorViewSet)
router.register(r'class-rooms', ClassRoomViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('import-xml/', xml_parser.import_xml_view, name='import-xml'),
    path('dashboard-stats/', xml_parser.dashboard_stats, name='dashboard-stats'),
    
    # Nuevas APIs para frontend
    path('schedules-list/', api.get_schedules_list, name='schedules-list'),
    path('schedules/<int:schedule_id>/calendar/', api.get_schedule_calendar, name='schedule-calendar'),
    path('schedules/<int:schedule_id>/timetable/', api.get_schedule_timetable, name='schedule-timetable'),
    path('schedules/<int:schedule_id>/conflicts/', api.get_conflict_analysis, name='schedule-conflicts'),
    path('schedules/<int:schedule_id>/rooms/', api.get_room_utilization, name='schedule-rooms'),
    path('analysis/workload/', api.get_workload_analysis, name='workload-analysis'),
    path('instructors-list/', api.get_instructors_list, name='instructors-list'),
    path('instructors/<int:instructor_id>/schedule/', api.get_instructor_schedule, name='instructor-schedule'),
    path('rooms-list/', api.get_rooms_list, name='rooms-list'),
    path('dashboard/stats/', api.get_dashboard_stats, name='dashboard-stats-api'),
]
