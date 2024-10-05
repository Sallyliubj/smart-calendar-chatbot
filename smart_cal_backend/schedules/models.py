from django.db import models
from users.models import UserProfile

class Schedule(models.Model):
    username = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    event_name = models.CharField(max_length=100)
    event_time = models.DateTimeField()
    event_type = models.CharField(max_length=50, choices=[('fixed', 'Fixed'), ('generated', 'Generated')])

    def __str__(self):
        return f"{self.username.username} - {self.event_name}"
