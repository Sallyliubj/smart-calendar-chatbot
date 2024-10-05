from django.http import JsonResponse
from .models import Meal

def get_daily_meals(request, user_id):
    meals = Meal.objects.filter(username__id=user_id)
    data = [
        {
            "meal_name": meal.meal_name,
            "calories": meal.calories,
            "recommendation_date": meal.recommendation_date
        } for meal in meals
    ]
    return JsonResponse(data, safe=False)
