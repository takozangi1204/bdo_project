from django.db import models


class Category(models.Model):
    """Event/To-Do category (e.g., MBUA514, MBUA532, BDO Project)."""
    cat_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, help_text='Hex colour, e.g. #E63946')
    bg = models.CharField(max_length=20, help_text='Background hex, e.g. #FFE0E3')
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class Event(models.Model):
    """Calendar event on a specific date with optional time and recurrence."""
    event_id = models.CharField(max_length=50, unique=True)
    series_id = models.CharField(max_length=50, blank=True, null=True,
                                  help_text='Shared ID for recurring event series')
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                  related_name='events', to_field='cat_id')
    title = models.CharField(max_length=200)
    url = models.URLField(blank=True, default='')
    start_time = models.CharField(max_length=10, blank=True, default='',
                                   help_text='e.g. 09:00')
    end_time = models.CharField(max_length=10, blank=True, default='',
                                 help_text='e.g. 17:00')

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f'{self.title} ({self.date})'


class Todo(models.Model):
    """To-do item on a specific date with completion state."""
    todo_id = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                  related_name='todos', to_field='cat_id')
    title = models.CharField(max_length=200)
    url = models.URLField(blank=True, default='')
    completed = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f'{self.title} ({"✓" if self.completed else "○"})'


class SchedulerSetting(models.Model):
    """Key-value settings store (startDate, endDate, viewMode)."""
    key = models.CharField(max_length=50, primary_key=True)
    value = models.TextField(default='')

    def __str__(self):
        return f'{self.key}={self.value}'


class BreakPeriod(models.Model):
    """School break period with start and end dates."""
    break_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, default='School Break')
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f'{self.name} ({self.start_date} – {self.end_date})'
