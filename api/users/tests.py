from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.authtoken import Token

class SignupViewTest(APITestCase):

    def setUp(self):
        self.url = reverse('signup')
        self.valid_payload = {
            "username": "testuser",
            "password": "strong_password_123",
            "birth_date": "2000-01-01",
            "can_be_contacted": "yes",
            "can_data_be_shared": "no"
        }
        self.invalid_payload = {
            "username": "",
            "password": "123"
        }

    def test_signup_success(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "Utilisateur crée avec succès")
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_signup_failure(self):
        response = self.client.post(self.url, self.invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)


class UserMeViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username = "existinguser", password = "strong_password_123"
        )
        self.token = Token.objects.create(user=self.user)
        self.url = reverse('user-me')

        

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token' + self.token.key)

    def test_get_user_me_authenticated(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'existinguser')