from django.db import models
from users.models import UserProfile

class Assignments(models.Model):
    username = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    assignment_name = models.CharField(max_length=100)
    due_date = models.DateTimeField()

    def __str__(self):
        return f"{self.username.username} - {self.assignment_name} due on {self.due_date}"
