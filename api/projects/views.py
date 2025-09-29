from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status, serializers
from .models import Project, Contributor
from .serializers import ProjectSerializer, ProjectSerializerDetail, ContributorSerializer
from .permissions import IsAuthor, IsContributor, IsAuthorOrContributor, IsProjectAuthor
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from users.models import CustomUser
from rest_framework.generics import GenericAPIView


class ProjectListCreateView(generics.ListCreateAPIView):
    """
    GET /api/projects/

    Récupère la liste de tous les projets de l'utilisateur connecté
    (qu’il soit contributeur ou auteur).

    ---
    POST /api/projects/

    Crée un nouveau projet.
    L'utilisateur authentifié devient automatiquement **l'auteur**.

    ### Exemple de corps de requête
    ```json
    {
        "title": "titre",
        "description": "description",
        "type": "BACKEND/FRONTEND/IOS/ANDROID"
    }
    ```

    ### Exemple de réponse
    ```json
    {
        "id": 1,
        "title": "titre",
        "description": "description",
        "type": "BACKEND",
        "created_time": "2025-09-10T12:11:06.912257Z"
    }
    ```
    """
    serializer_class = ProjectSerializer
    # Un utilisateur doit être connecté et auteur OU contributeur du projet pour y accéder
    permission_classes = [IsAuthenticated, IsAuthorOrContributor]

    def get_queryset(self):
        # Retourne uniquement les projets où l’utilisateur est contributeur ou auteur
        return Project.objects.filter(contributors__user=self.request.user)

    def perform_create(self, serializer):
        # Lors de la création, l’utilisateur connecté est défini comme auteur
        serializer.save(author=self.request.user)


class ProjectDetailView(APIView):
    """
    GET /api/projects/{project-id}/
    Récupère les détails d'un projet.

    PUT /api/projects/{project-id}/
    Met à jour les informations d'un projet.

    DELETE /api/projects/{project-id}/
    Supprime un projet (**réservé à l'auteur**).
    """
    serializer_class = ProjectSerializerDetail
    permission_classes = [IsAuthenticated]  
    lookup_field = 'id'

    def get_permissions(self):
        # Permissions dynamiques selon la méthode
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsAuthorOrContributor()]
        elif self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated(), IsAuthor()]
        return super().get_permissions()

    def get_object(self, project_id):
        # Récupère un projet par son ID ou renvoie 404
        return get_object_or_404(Project, id=project_id)

    def get(self, request, project_id):
        # Consultation des détails d’un projet
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        serializer = self.serializer_class(project)
        return Response(serializer.data)

    def put(self, request, project_id):
        # Mise à jour des informations du projet (réservé à l’auteur)
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        serializer = self.serializer_class(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, project_id):
        # Suppression d’un projet (réservée à l’auteur)
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ContributorView(APIView):
    """
    GET /api/projects/{project-id}/contributors/
    Liste les contributeurs d’un projet.

    POST /api/projects/{project-id}/contributors/
    Ajoute un nouveau contributeur (réservé à l’auteur du projet).

    ### Exemple de corps de requête
    ```json
    {
        "user": 2
    }
    ```

    ### Exemple de réponse
    ```json
    {
        "message": "Le contributeur user2 a bien été ajouté au projet.",
        "contributor": {
            "id": 5,
            "user": 2,
            "project": 1
        }
    }
    ```
    DELETE /api/projects/{project-id}/contributors/{id}/
    Supprime un contributeur d’un projet (**réservé à l’auteur**).

    ### Exemple de corps de requête
    ```json
    {
        "user": 2
    }
    ```

    ### Exemple de réponse
    ```json
    {
        "message": "Le contributeur user2 a été supprimé du projet."
    }
    ```
    """
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self, project_id):
        return Contributor.objects.filter(project_id=project_id)

    def get(self, request, project_id):
        # Lister les contributeurs d’un projet
        project = Project.objects.get(pk=project_id)
        self.check_object_permissions(request, project)

        contributors = self.get_queryset(project_id)
        serializer = ContributorSerializer(contributors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, project_id):
        # Ajouter un contributeur
        project = Project.objects.get(pk=project_id)
        self.check_object_permissions(request, project)

        if project.author != request.user:
            raise PermissionDenied("Seul l'auteur du projet peut ajouter des contributeurs")

        serializer = ContributorSerializer(data=request.data, context={"project": project})
        serializer.is_valid(raise_exception=True)
        serializer.save(project=project)

        return Response(
            {
                "message": f"Le contributeur {serializer.data['user']} a bien été ajouté au projet.",
                "contributor": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, project_id):
        # Supprimer un contributeur
        project = Project.objects.get(pk=project_id)
        self.check_object_permissions(request, project)

        if project.author != request.user:
            raise PermissionDenied("Seul l'auteur du projet peut supprimer des contributeurs")

        username = request.data.get("user")
        if not username:
            raise ValidationError({"user": "Vous devez fournir un username."})

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            raise NotFound({"user": "Utilisateur introuvable."})

        try:
            contributor = Contributor.objects.get(project=project, user=user)
        except Contributor.DoesNotExist:
            raise ValidationError({"user": "Cet utilisateur n’est pas contributeur de ce projet."})

        if contributor.user == project.author:
            raise ValidationError("Vous ne pouvez pas supprimer l'auteur du projet.")

        contributor.delete()

        return Response(
            {"message": f"Le contributeur {username} a bien été supprimé du projet."},
            status=status.HTTP_200_OK
        )


