from django.test import TestCase, Client
from django.urls import reverse
from users.models import UserProfile

class UserTestCase(TestCase):
    def setUp(self):
        # Set up initial test data
        self.user = UserProfile.objects.create(username='testuser', email='testuser@example.com')
        self.client = Client()

    def test_user_profile_creation(self):
        # Test user profile creation
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'testuser@example.com')
