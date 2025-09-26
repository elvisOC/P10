from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Project, Contributor
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectContributorTests(APITestCase):


    def setUp(self):
        # Création d'utilisateurs
        self.user1_data = {
            "username": "user1",
            "password": "Pass1234",
            "birth_date": "1990-01-01",
            "can_be_contacted": "no",
            "can_data_be_shared": "no"
        }
        self.user2_data = {
            "username": "user2",
            "password": "Pass1234",
            "birth_date": "1992-05-10",
            "can_be_contacted": "yes",
            "can_data_be_shared": "yes"
        }

        self.user3_data = {
            "username": "user3",
            "password": "Pass1234",
            "birth_date": "1994-07-31",
            "can_be_contacted": "no",
            "can_data_be_shared": "yes"
        }
        

        # Création directe dans la base
        self.signup_url = reverse("signup")
        self.client.post(self.signup_url, self.user1_data, format="json")
        self.client.post(self.signup_url, self.user2_data, format="json")
        self.client.post(self.signup_url, self.user3_data, format="json")

    def authenticate(self, user):
        response = self.client.post(reverse("token_obtain_pair"), {
            "username": user["username"],
            "password": "Pass1234"
        }, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_full_project_contributor(self):
        # Création d'un projet par user1
        self.projects_url = reverse("project_list_create")
        self.authenticate(self.user1_data)
        project_data = {"title": "Mon Projet", "description": "Desc", "type": "BACKEND"}
        response = self.client.post(self.projects_url, project_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project_id = response.data["id"]

        # URLs dynamiques pour détails et contributeurs
        project_detail_url = reverse("project_view", args=[project_id])
        contributors_url = reverse("contributor_list_create", args=[project_id])

        # Accès au projet par l'auteur (user1)
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Mon Projet")

        # Accès interdit pour user2 (non contributeur)
        self.authenticate(self.user2_data)
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Ajout de user2 comme contributeur par user1
        self.authenticate(self.user1_data)
        response = self.client.post(contributors_url, {"user": "user2"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Le contributeur user2 a bien été ajouté", response.data["message"])

        # Vérification que user2 est bien contributeur
        response = self.client.get(project_detail_url)
        contributor_usernames = [c["user"] for c in response.data["contributors"]]
        self.assertIn("user2", contributor_usernames)

        # Vérification que user2 accéde au projet
        self.authenticate(self.user2_data)
        reponse = self.client.get(project_detail_url)
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Mon Projet")

        # Récupération de l'id user2 (users/me/)
        self.authenticate(self.user2_data)
        self.me_url = reverse("user_me")
        response = self.client.get(self.me_url)
        user2_id = response.data["id"]

        self.authenticate(self.user1_data)
        response = self.client.get(self.me_url)
        user1_id = response.data["id"]

        # Suppression du contributeur user2 par l'auteur
        contributor = Contributor.objects.get(project_id=project_id, user=user2_id)
        contributor_delete_url = reverse("contributor_delete", args=[project_id, contributor.id])
        response = self.client.delete(contributor_delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Le contributeur user2 a été supprimé", response.data["message"])

        # Tentative de suppression de l'auteur (user1) → doit échouer
        author_contrib = Contributor.objects.get(project_id=project_id, user=user1_id)
        contributor_delete_url = reverse("contributor_delete", args=[project_id, author_contrib.id])
        response = self.client.delete(contributor_delete_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any("Vous ne pouvez pas supprimer l'auteur" in msg for msg in response.data))
    
