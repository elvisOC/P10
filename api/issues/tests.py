from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from projects.models import Project, Contributor
from issues.models import Issue, Comment
from rest_framework.exceptions import ValidationError

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
        self.project_id = response.data["id"]

        # URLs dynamiques
        self.contributors_url = reverse("contributor_list_create", args=[self.project_id])
        self.issues_url = reverse("issues_list", args=[self.project_id])

        # Ajout de user2 comme contributeur
        self.client.post(self.contributors_url, {"user": "user2"}, format="json")

    # Authentification et token dans l'en-tête HTTP
    def authenticate(self, user):
        response = self.client.post(reverse("token_obtain_pair"), {
            "username": user["username"],
            "password": "Pass1234"
        }, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    # Création d'issue par un contributeur du projet
    def test_contributor_can_create_issue(self):
        self.authenticate(self.user1_data)
        data = {"title": "Bug critique", "description": "Crash sur la page d'accueil", "priority": "LOW", "balise": "BUG"}
        response = self.client.post(self.issues_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["issue"]["title"], "Bug critique")
        self.assertEqual(response.data["issue"]["progress"], "TODO")
        self.assertEqual(response.data["issue"]["assignee"], "user1")

    # Création d'issue par un contributeur et assignement d'un autre contributeur
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

    # Modification d'un contributeur assigné dans une issue existante
    def test_contributor_can_patch_issue_to_another_contributor(self):
        self.authenticate(self.user1_data)
        data = {
            "title": "Nouvelle feature 2",
            "description": "Ajouter un bouton",
            "priority": "LOW",
            "balise": "BUG"
        }
        response = self.client.post(self.issues_url, data, format="json")
        issue_id = response.data["issue"]["id"]
        issue_detail_url = reverse("issue_detail", args=[self.project_id, issue_id])
        patch_data = {"assignee": "user2"}
        response = self.client.patch(issue_detail_url, patch_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["issue"]["assignee"], "user2")

    # Assignement d'un issue à un non contributeur du projet associé
    def test_contributor_cannot_assign_issue_to_non_contributor(self):
        self.authenticate(self.user1_data)
        data = {"title": "Bug suspect", "description": "Erreur d'accès", "assignee": "user3"}
        response = self.client.post(self.issues_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("n'est pas contributeur", str(response.data))

    # Création d'un issue avec formulaire incomplet
    def test_create_issue_validation_error(self):
        self.authenticate(self.user1_data)
        response = self.client.post(self.issues_url, data={"description": "sans titre"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", str(response.data["message"]))

    # Mise à jour partiel et test message
    def test_issue_partial_update_message(self):
        self.authenticate(self.user1_data)
        issue = Issue.objects.create(title="Init", description="Desc", author=User.objects.get(username="user1"), project=Project.objects.get(id=self.project_id))
        url = reverse("issue_detail", args=[self.project_id, issue.id])
        response = self.client.put(url, data={"title": "Updated"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("mise à jour", response.data["message"])

    # Suppression d'une issue et test message
    def test_destroy_issue_message(self):
        self.authenticate(self.user1_data)
        issue = Issue.objects.create(title="ToDelete", description="Desc", author=User.objects.get(username="user1"), project=Project.objects.get(id=self.project_id))
        url = reverse("issue_detail", args=[self.project_id, issue.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("supprimée", response.data["message"])



