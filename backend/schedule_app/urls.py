from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomViewSet, InstructorViewSet, CourseViewSet,
    ClassViewSet, StudentViewSet,
    TimeSlotViewSet, ClassInstructorViewSet, ClassRoomViewSet
)
from . import xml_parser
from . import generation_api as generation_api

router = DefaultRouter()
router.register(r'rooms', RoomViewSet)
router.register(r'instructors', InstructorViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'classes', ClassViewSet)
router.register(r'students', StudentViewSet)
router.register(r'timeslots', TimeSlotViewSet)
router.register(r'class-instructors', ClassInstructorViewSet)
router.register(r'class-rooms', ClassRoomViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('import-xml/', xml_parser.import_xml_view, name='import-xml'),
    path('dashboard-stats/', xml_parser.dashboard_stats, name='dashboard-stats'),
    
    # === API Sistema Híbrido ===
    path('generate/datasets/', generation_api.list_datasets, name='list-datasets'),
    path('generate/constraints/', generation_api.get_constraints, name='get-constraints'),
    path('generate/schedule/', generation_api.generate_schedule, name='generate-schedule'),
    path('generate/upload/', generation_api.generate_from_upload, name='generate-from-upload'),
    path('generate/prepare/', generation_api.prepare_datasets, name='prepare-datasets'),
    path('generate/last/', generation_api.get_last_schedule, name='get-last-schedule'),
    path('generate/saved/', generation_api.list_saved_schedules, name='list-saved-schedules'),
    path('generate/saved/<int:schedule_id>/', generation_api.get_saved_schedule, name='get-saved-schedule'),
    path('generate/saved/<int:schedule_id>/delete/', generation_api.delete_schedule, name='delete-schedule'),
]
