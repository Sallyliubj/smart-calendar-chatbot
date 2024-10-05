from django.http import JsonResponse
from .models import Schedule

def get_user_schedule(request, user_id):
    schedules = Schedule.objects.filter(username__id=user_id)
    data = [
        {
            "event_name": schedule.event_name,
            "event_time": schedule.event_time,
            "event_type": schedule.event_type
        } for schedule in schedules
    ]
    return JsonResponse(data, safe=False)
