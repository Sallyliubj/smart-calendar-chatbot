from django.db import models
from users.models import UserProfile

class Meal(models.Model):
    username = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    meal_name = models.CharField(max_length=100)
    calories = models.IntegerField()
    recommendation_date = models.DateField()

    def __str__(self):
        return f"{self.username.username} - {self.meal_name} ({self.recommendation_date})"
