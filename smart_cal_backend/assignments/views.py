from django.http import JsonResponse
from .models import Assignments

def get_user_assignments(request, user_id):
    assignments = Assignments.objects.filter(username__id=user_id)
    data = [
        {
            "assignment_name": assignment.assignment_name,
            "due_date": assignment.due_date
        } for assignment in assignments
    ]
    return JsonResponse(data, safe=False)
