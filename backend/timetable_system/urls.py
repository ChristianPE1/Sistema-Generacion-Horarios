"""
URL configuration for timetable_system project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('schedule_app.urls')),
]
