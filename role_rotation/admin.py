from django.contrib import admin
from .models import WeeklyTask, EmailRecipient


@admin.register(WeeklyTask)
class WeeklyTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'day_of_week', 'time', 'assigned_person', 'created_at')
    list_filter = ('day_of_week',)
    search_fields = ('title', 'description', 'assigned_person', 'time')


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'email')
    list_editable = ('is_active',)