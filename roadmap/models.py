from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Phase(models.Model):
    phase_id = models.CharField(
        max_length=50, 
        unique=True,
        help_text = 'Example: Setup, Empathise, Milestone',
        )
    name = models.CharField(max_length=100)
    colour = models.CharField(
        max_length = 100, 
        help_text = 'Example: #6B8DE3',
    )
    bg = models.CharField(
        max_length = 20,
        help_text = 'Example: #E0E8FF',
    )
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('inprogress', 'In Progress'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=200)
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='tasks')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    deliverables = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title} ({self.phase.name})'