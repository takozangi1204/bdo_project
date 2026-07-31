from django.urls import path 
from. import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/data/', views.get_roadmap_data, name='get_data'),
    path('api/task/save/', views.save_task, name='save_task'),
    path('api/task/delete/<str:task_id>/', views.delete_task, name='delete_task'),
    path('api/tasks/import/', views.import_tasks, name='import_tasks'),
    path('api/tasks/reorder/', views.reorder_tasks, name='reorder_tasks'),
    path('api/tasks/clear/', views.clear_all_tasks, name='clear_all_tasks'),
]