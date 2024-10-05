from django.urls import path
from . import views

urlpatterns = [
    path('schedule/<int:user_id>/', views.get_user_schedule, name='user_schedule'),
]
