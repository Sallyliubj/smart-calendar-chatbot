from django.urls import path
from . import views

urlpatterns = [
    path('assignments/<int:user_id>/', views.get_user_assignments, name='user_assignments'),
]