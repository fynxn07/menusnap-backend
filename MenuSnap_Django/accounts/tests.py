from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import User


# Create your tests here.
class RegisterApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("register")

    def test_register_success(self):
        data = {
            "restaurant_name": "Food Hub",
            "owner_name": "shibu",
            "email": "shibu@test.com",
            "phone": "9876543210",
            "password": "12345678",
            "confirm_password": "12345678",
        }

        res = self.client.post(self.url, data)
        print("\nSTATUS:", res.status_code)
        print("Response:", res.data)

        self.assertEqual(res.status_code, 201)


class LoginApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("login")

        self.user = User.objects.create_user(
            email="login@test.com", password="12345678", name="test"
        )

    def test_login_success(self):
        data = {"email": "login@test.com", "password": "12345678"}

        res = self.client.post(self.url, data)
        print("\nSTATUS:", res.status_code)
        print("\nResponse:", res.data)

        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)


class ProfileApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("profile")

        self.user = User.objects.create_user(
            email="profile@test.com", password="12345678", name="Profile User"
        )

        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        res = self.client.get(self.url)

        print("\nStatus:", res.status_code)
        print("Response:", res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["email"], "profile@test.com")


class LogoutApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("logout")

    def test_logout(self):
        res = self.client.post(self.url)

        print("\nStatus:", res.status_code)
        print("Response:", res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["detail"], "Logged out successfully")
