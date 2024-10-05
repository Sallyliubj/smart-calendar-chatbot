from django.urls import path
from . import views

urlpatterns = [
    path('meals/<int:user_id>/', views.get_daily_meals, name='daily_meals'),
]
