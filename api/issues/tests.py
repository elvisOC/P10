from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from projects.models import Project, Contributor
from issues.models import Issue

User = get_user_model()


class IssueFlowTests(APITestCase):
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

        # Création des comptes
        self.signup_url = reverse("signup")
        self.client.post(self.signup_url, self.user1_data, format="json")
        self.client.post(self.signup_url, self.user2_data, format="json")
        self.client.post(self.signup_url, self.user3_data, format="json")

        # Création d'un projet par user1
        self.projects_url = reverse("project_list_create")
        self.authenticate(self.user1_data)
        project_data = {"title": "Mon Projet", "description": "Desc", "type": "BACKEND"}
        response = self.client.post(self.projects_url, project_data, format="json")
        self.project_id = response.data["id"]  # <- stocké comme attribut

        # URLs dynamiques
        contributors_url = reverse("contributor_list_create", args=[self.project_id])
        self.issues_url = reverse("issues_list", args=[self.project_id])

        # Ajout de user2 comme contributeur
        self.client.post(contributors_url, {"user": "user2"}, format="json")

    def authenticate(self, user):
        response = self.client.post(reverse("token_obtain_pair"), {
            "username": user["username"],
            "password": "Pass1234"
        }, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    # Un contributeur peut créer une issue avec titre et description (en laissant progress par défaut)
    def test_contributor_can_create_issue(self):
        self.authenticate(self.user1_data)
        data = {"title": "Bug critique", "description": "Crash sur la page d'accueil", "priority": "LOW", "balise": "BUG"}
        response = self.client.post(self.issues_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["issue"]["title"], "Bug critique")
        self.assertEqual(response.data["issue"]["progress"], "TODO")
        self.assertEqual(response.data["issue"]["assignee"], "user1")

    # Un contributeur peut assigner une issue à un autre contributeur
    def test_contributor_can_create_issue_to_another_contributor(self):
        self.authenticate(self.user1_data)
        data = {
            "title": "Nouvelle feature",
            "description": "Ajouter un bouton",
            "priority": "LOW",
            "balise": "BUG",
            "assignee": "user2"
        }
        response = self.client.post(self.issues_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["issue"]["assignee"], "user2")

    def test_contributor_can_patch_issue_to_another_contributor(self):
        self.authenticate(self.user1_data)
        data = {
            "title": "Test assigner",
            "description": "Changement user1 user2",
            "priority": "LOW",
            "balise": "BUG"
        }

        # Création de l'issue
        response = self.client.post(self.issues_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        issue_id = response.data["issue"]["id"]

        issue_detail_url = reverse("issue_detail", args=[self.project_id, issue_id])

        patch_data = {"assignee": "user2"}
        response = self.client.patch(issue_detail_url, patch_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["issue"]["assignee"], "user2")

    # Impossible d’assigner une issue à quelqu’un qui n’est pas contributeur
    def test_contributor_cannot_assign_issue_to_non_contributor(self):
        self.authenticate(self.user1_data)
        data = {"title": "Bug suspect", "description": "Erreur d'accès", "assignee": "user3"}
        response = self.client.post(self.issues_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("n'est pas contributeur", str(response.data))
