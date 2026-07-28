from django.contrib import admin
from .models import Category, Event, Todo, SchedulerSetting, BreakPeriod


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('cat_id', 'name', 'color', 'bg', 'sort_order')
    ordering = ('sort_order',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'title', 'date', 'category', 'start_time', 'end_time', 'series_id')
    list_filter = ('category', 'date')
    ordering = ('date',)


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ('todo_id', 'title', 'date', 'category', 'completed', 'sort_order')
    list_filter = ('category', 'completed', 'date')
    ordering = ('sort_order', 'created_at')


@admin.register(SchedulerSetting)
class SchedulerSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')


@admin.register(BreakPeriod)
class BreakPeriodAdmin(admin.ModelAdmin):
    list_display = ('break_id', 'name', 'start_date', 'end_date')
    ordering = ('start_date',)
