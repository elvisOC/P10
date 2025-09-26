from django.shortcuts import render
from rest_framework import generics, status, serializers
from .models import Project, Contributor
from .serializers import ProjectSerializer, ProjectSerializerDetail, ContributorSerializer
from .permissions import IsAuthor, IsContributor, IsAuthorOrContributor, IsProjectAuthor
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404


class ProjectListCreateView(generics.ListCreateAPIView):
    """
    GET /api/projects/

    Récupère la liste de tous les projets de l'utilisateur connecté, contributeur ou auteur.

    POST /api/projects/

    Crée un nouveau projet.
    L'utilisateur authentifié devient automatiquement **l'auteur**.

    Exemple de corps de requête :
    ```json
    {
        "title" : "titre",
        "description" : "description",
        "type" : "BACKEND/FRONTEND/IOS/ANDROID"
    }
    ```
    Exemple de réponse :
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
    permission_classes = [IsAuthenticated, IsAuthorOrContributor]
    
    def get_queryset(self):
        return Project.objects.filter(contributors__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        
class ProjectDetailView(APIView):
    """
    GET /api/projects/{project-id}/
    Récupère les détails d'un projet.

    PUT /api/projects/{project-id}/
    Met à jour les informations d'un projet.

    DELETE /api/projects/{project-id}/
    Supprime un projet (réservé à l'auteur).
    """

    serializer_class = ProjectSerializerDetail
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsAuthorOrContributor()]
        elif self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated(), IsAuthor()]
        return super().get_permissions()

    def get_object(self, project_id):
        return get_object_or_404(Project, id=project_id)

    def get(self, request, project_id):
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        serializer = self.serializer_class(project)
        return Response(serializer.data)

    def put(self, request, project_id):
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        serializer = self.serializer_class(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, project_id):
        project = self.get_object(project_id)
        self.check_object_permissions(request, project)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class ContributorListCreateView(generics.ListCreateAPIView):
    serializer_class = ContributorSerializer
    permission_classes = [IsAuthenticated, IsAuthor]
    
    def get_queryset(self):
        return Contributor.objects.filter(id=self.kwargs['project_id'])
    
    def perform_create(self, serializer):
        serializer.save()
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        project_id = self.kwargs['project_id']
        project = Project.objects.get(id=project_id)
        context['project'] = project
        return context

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(pk=self.kwargs['project_id'])
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
                {
                    "message": str(e.detail)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    
class ContributorDeleteView(generics.DestroyAPIView):
    serializer_class = ContributorSerializer
    permission_classes = [IsAuthenticated, IsProjectAuthor]
    lookup_field = 'id'

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Contributor.objects.filter(project_id=project_id)

    def perform_destroy(self, instance):
        if instance.project.author != self.request.user:
            raise PermissionDenied("Seul l'auteur du projet peut supprimer un contributeur.")
        if instance.project.author == instance.user:
            raise ValidationError("Vous ne pouvez pas supprimer l'auteur du projet")
        instance.delete()

    def delete(self, request, project_id, id):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": f"Le contributeur {instance.user.username} a été supprimé du projet."},
            status=status.HTTP_200_OK
        )