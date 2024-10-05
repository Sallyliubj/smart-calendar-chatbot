from django.test import TestCase, Client
from django.urls import reverse
from users.models import UserProfile
from nutrition.models import Meal
from datetime import date

class NutritionTestCase(TestCase):
    def setUp(self):
        # Set up initial test data
        self.user = UserProfile.objects.create(username='testuser', email='testuser@example.com')
        self.meal = Meal.objects.create(username=self.user, meal_name='Test Meal', calories=500, recommendation_date=date.today())
        self.client = Client()

    def test_get_daily_meals(self):
        # Test retrieving the user's daily meal recommendation
        url = reverse('daily_meals', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Meal', str(response.content))