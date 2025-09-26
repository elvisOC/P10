from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import CustomUser


class UserFlowTests(APITestCase):

    def setUp(self):
        # Données utilisées pour créer un utilisateur
        self.signup_url = reverse("signup")   
        self.token_url = reverse("token_obtain_pair")  
        self.me_url = reverse("user_me")      
        self.user_data = {
            "username": "testuser",
            "password": "StrongPass123",
            "birth_date": "1994-07-31",
            "can_be_contacted": "yes",
            "can_data_be_shared": "no"
        }

    def test_full_user_flow(self):

        # Création de compte
        response = self.client.post(self.signup_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)
        self.assertEqual(CustomUser.objects.count(), 1)

        # Récupération du token JWT
        response = self.client.post(self.token_url, {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        access_token = response.data["access"]

        # Ajout du token dans le header pour les prochaines requêtes
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # Récupération des données utilisateur (/me/)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user_data["username"])
        self.assertEqual(response.data["can_be_contacted"], True)

        # Mise à jour complète (PUT)
        update_data = {
            "username": "newuser",
            "birth_date": "1994-07-30",
            "can_be_contacted": "no",
            "can_data_be_shared": "yes"
        }
        response = self.client.put(self.me_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "newuser")
        self.assertEqual(response.data["can_data_be_shared"], True)

        # Mise à jour partielle (PATCH)
        response = self.client.patch(self.me_url, {"can_be_contacted": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["can_be_contacted"], True)

        # Suppression de compte
        response = self.client.delete(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(CustomUser.objects.count(), 0)


    def test_login_with_wrong_credentials(self):

        # Mauvais mot de passe
        response = self.client.post(self.token_url, {
            "username": "testuser",
            "password": "WrongPass999"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

        # Mauvais nom d'utilisateur
        response = self.client.post(self.token_url, {
            "username": "unknownuser",
            "password": "StrongPass123"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)