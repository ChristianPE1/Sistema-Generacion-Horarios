from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomViewSet, InstructorViewSet, CourseViewSet,
    ClassViewSet, StudentViewSet, ScheduleViewSet,
    TimeSlotViewSet, ClassInstructorViewSet, ClassRoomViewSet
)
from . import xml_parser

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
]
