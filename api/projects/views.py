from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status, serializers
from .models import Project, Contributor
from .serializers import ProjectSerializer, ProjectSerializerDetail, ContributorSerializer
from .permissions import IsAuthor, IsContributor, IsAuthorOrContributor, IsProjectAuthor
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q


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
    permission_classes = [IsAuthenticated]  # La vérification fine se fait dans get_permissions()
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


class ContributorListCreateView(generics.ListCreateAPIView):
    """
    GET /api/projects/{project-id}/contributors/
    Liste les contributeurs d’un projet.

    POST /api/projects/{project-id}/contributors/
    Ajoute un nouveau contributeur (réservé à l’auteur du projet).

    ### Exemple de corps de requête
    ```json
    {
        "user": 2,
        "role": "CONTRIBUTOR"
    }
    ```

    ### Exemple de réponse
    ```json
    {
        "message": "Le contributeur user2 a bien été ajouté au projet.",
        "contributor": {
            "id": 5,
            "user": 2,
            "role": "CONTRIBUTOR",
            "project": 1
        }
    }
    ```
    """
    serializer_class = ContributorSerializer
    # Seul un auteur authentifié peut gérer les contributeurs
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self):
        # Liste des contributeurs liés à un projet donné
        return Contributor.objects.filter(id=self.kwargs['project_id'])

    def perform_create(self, serializer):
        # Sauvegarde d’un nouveau contributeur
        serializer.save()

    def get_serializer_context(self):
        # Passe l’objet projet au serializer pour validation
        context = super().get_serializer_context()
        project_id = self.kwargs['project_id']
        project = Project.objects.get(id=project_id)
        context['project'] = project
        return context

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(pk=self.kwargs['project_id'])
        # Vérifie que l’utilisateur a les permissions sur ce projet
        self.check_object_permissions(request, project)

        if project.author != request.user:
            raise PermissionDenied("Seul l'auteur du projet peut ajouter des contributeurs")

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    "message": f"Le contributeur {serializer.data['user']} a bien été ajouté au projet.",
                    "contributor": serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except serializers.ValidationError as e:
            return Response(
                {"message": str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ContributorDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/projects/{project-id}/contributors/{id}/
    Supprime un contributeur d’un projet (**réservé à l’auteur**).

    ### Exemple de réponse
    ```json
    {
        "message": "Le contributeur user2 a été supprimé du projet."
    }
    ```
    """
    serializer_class = ContributorSerializer
    # Seul l’auteur d’un projet peut retirer un contributeur
    permission_classes = [IsAuthenticated, IsProjectAuthor]
    lookup_field = 'id'

    def get_queryset(self):
        # On récupère les contributeurs liés au projet
        project_id = self.kwargs['project_id']
        return Contributor.objects.filter(project_id=project_id)

    def perform_destroy(self, instance):
        # L’auteur ne peut pas se supprimer lui-même
        if instance.project.author != self.request.user:
            raise PermissionDenied("Seul l'auteur du projet peut supprimer un contributeur.")
        if instance.project.author == instance.user:
            raise ValidationError("Vous ne pouvez pas supprimer l'auteur du projet")
        instance.delete()

    def delete(self, request, project_id, id):
        # Suppression d’un contributeur
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": f"Le contributeur {instance.user.username} a été supprimé du projet."},
            status=status.HTTP_200_OK
        )
