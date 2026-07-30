from django.urls import path
from . import views

urlpatterns = [
    path('', views.cadence_dashboard, name='role_rotation_dashboard'),
    path('', views.cadence_dashboard, name='cadence_dashboard'),
    path('dashboard/', views.cadence_dashboard, name='role_rotation_dashboard_alt'),
    path('dashboard/', views.cadence_dashboard, name='cadence_dashboard_alt'),
    path('api/tasks/', views.get_tasks, name='role_rotation_get_tasks'),
    path('api/tasks/', views.get_tasks, name='cadence_get_tasks'),
    path('api/task/save/', views.save_task, name='role_rotation_save_task'),
    path('api/task/save/', views.save_task, name='cadence_save_task'),
    path('api/task/toggle/<int:task_id>/', views.toggle_task, name='role_rotation_toggle_task'),
    path('api/task/toggle/<int:task_id>/', views.toggle_task, name='cadence_toggle_task'),
    path('api/task/delete/<int:task_id>/', views.delete_task, name='role_rotation_delete_task'),
    path('api/task/delete/<int:task_id>/', views.delete_task, name='cadence_delete_task'),
    path('api/tasks/reset/', views.reset_weekly_progress, name='role_rotation_reset_progress'),
    path('api/tasks/reset/', views.reset_weekly_progress, name='cadence_reset_progress'),
    path('api/send-reminder/', views.trigger_friday_reminder, name='role_rotation_trigger_reminder'),
    path('api/send-reminder/', views.trigger_friday_reminder, name='cadence_trigger_reminder'),
    path('api/send-monday-reminder/', views.trigger_monday_reminder, name='role_rotation_trigger_monday_reminder'),
    path('api/send-monday-reminder/', views.trigger_monday_reminder, name='cadence_trigger_monday_reminder'),
    path('download-template/<str:recipient>/', views.download_template, name='role_rotation_download_template'),
    path('download-template/<str:recipient>/', views.download_template, name='cadence_download_template'),
]