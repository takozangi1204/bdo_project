from django.db import models


class WeeklyTask(models.Model):
    CADENCE_TYPES = [
        (1, 'Daily Cadence'),
        (2, 'Weekly Cadence'),
        (3, 'Bi-Weekly Cadence'),
        (4, 'Monthly Cadence'),
        (5, 'Ad-Hoc / Special'),
    ]
    WEEKDAYS = CADENCE_TYPES  # Backward compatibility alias

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    day_of_week = models.IntegerField(choices=CADENCE_TYPES, default=1, verbose_name="Cadence Group")
    time = models.CharField(max_length=50, blank=True, help_text="Deadline or schedule time, e.g. 11:00 AM")
    assigned_person = models.CharField(max_length=100, blank=True, help_text="Person assigned to this task")
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        assigned = f" ({self.assigned_person})" if self.assigned_person else ""
        time_str = f" [{self.time}]" if self.time else ""
        return f'{self.get_day_of_week_display()}: {self.title}{time_str}{assigned}'


class EmailRecipient(models.Model):
    name = models.CharField(max_length=100, help_text="Team Member Name, e.g. Taiki")
    email = models.EmailField(unique=True, help_text="Email address for weekly role reminders")
    is_active = models.BooleanField(default=True, help_text="Checked = Receives weekly Monday emails")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Email Recipient"
        verbose_name_plural = "Email Recipients"

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} <{self.email}> ({status})"
