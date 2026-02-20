from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from restaurants.models import Restaurant

from .models import MenuCategory

# Create your tests here.


class MenuCategoryTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="menu@test.com",
            password="12345678",
            name="Menu User",
        )

        self.restaurant = Restaurant.objects.create(name="Test Hotel", owner=self.user)

        self.user.restaurant = self.restaurant
        self.user.save()

        self.client.force_authenticate(user=self.user)
        self.url = "/menu/add_categories/"

    def test_create_category(self):
        data = {"name": "Starters", "display_order": 1}
        res = self.client.post(self.url, data)
        print("\nStatus:", res.status_code, 201)
        print("Response", res.data)

        self.assertEqual(res.status_code, 201)
        self.assertEqual(MenuCategory.objects.count(), 1)

    def test_list_category(self):

        MenuCategory.objects.create(name="Starters", restaurant=self.restaurant)

        url = "/menu/categories/"
        res = self.client.get(url)

        print("/status:", res.status_code)
        print("response:", res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
