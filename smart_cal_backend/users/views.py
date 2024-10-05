from django.shortcuts import render
from django.db import models

class UserProfile(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    sleep_habit = models.CharField(max_length=100)
    sports_interest = models.CharField(max_length=100)
    dietary_preference = models.CharField(max_length=100)

    def __str__(self):
        return self.name
