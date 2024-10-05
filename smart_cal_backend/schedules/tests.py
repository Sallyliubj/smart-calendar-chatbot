from django.test import TestCase, Client
from django.urls import reverse
from users.models import UserProfile
from schedules.models import Schedule
from datetime import datetime
from django.utils import timezone

class ScheduleTestCase(TestCase):
    def setUp(self):
        # Set up initial test data
        self.user = UserProfile.objects.create(username='testuser', email='testuser@example.com')
        self.schedule = Schedule.objects.create(username=self.user, event_name='Test Event', event_time=timezone.now(), event_type='fixed')
        self.client = Client()

    def test_get_user_schedule(self):
        # Test retrieving the user's schedule
        url = reverse('user_schedule', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Event', str(response.content))
        print("User schedule retrieved successfully:", response.content)