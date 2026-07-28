from django.contrib import admin
from .models import Phase, Task 
# Register your models here.

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ('phase_id', 'name', 'colour', 'bg', 'order')
    ordering = ('order', )

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'phase', 'start_date', 'end_date', 'status')
    list_filter = ('phase', 'status')
    search_fields = ('title', 'deliverables') 
    
