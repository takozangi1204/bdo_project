from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='scheduler_index'),
    path('api/data/', views.get_scheduler_data, name='scheduler_data'),
    path('api/event/save/', views.save_event, name='scheduler_save_event'),
    path('api/event/delete/<str:event_id>/', views.delete_event, name='scheduler_delete_event'),
    path('api/event/delete-series/<str:series_id>/', views.delete_event_series, name='scheduler_delete_event_series'),
    path('api/todo/save/', views.save_todo, name='scheduler_save_todo'),
    path('api/todo/delete/<str:todo_id>/', views.delete_todo, name='scheduler_delete_todo'),
    path('api/todo/toggle/<str:todo_id>/', views.toggle_todo, name='scheduler_toggle_todo'),
    path('api/todo/reorder/', views.reorder_todos, name='scheduler_reorder_todos'),
    path('api/categories/save/', views.save_categories, name='scheduler_save_categories'),
    path('api/category-items/delete/', views.delete_selected_category_items, name='scheduler_delete_category_items'),
    path('api/settings/save/', views.save_settings, name='scheduler_save_settings'),
    path('api/clear-all/', views.clear_all, name='scheduler_clear_all'),
    path('api/import/', views.import_data, name='scheduler_import'),
]
