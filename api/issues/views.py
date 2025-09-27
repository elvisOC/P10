from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Issue, Comment
from .serializers import IssueSerializer, CommentSerializer, ContributorSerializer
from .permissions import IsContributor, IsAuthor
from projects.models import Contributor, Project


class IssuesListCreateView(generics.ListCreateAPIView):
    """
    GET /api/projects/{project-id}/issues/

    Récupère la liste des issues (tickets) d’un projet.

    ---
    POST /api/projects/{project-id}/issues/

    Crée une nouvelle issue dans le projet.

    ### Exemple de corps de requête
    ```json
    {
        "title": "Bug de connexion",
        "description": "Impossible de se connecter avec Google",
        "assignee": 3,
        "priority": "HIGH",
        "balise": "BUG"
        "status": "TODO"
    }
    ```

    ### Exemple de réponse
    ```json
    {
        "message": "L'issue 'Bug de connexion' a bien été créée.",
        "issue": {
            "id": 1,
            "title": "Bug de connexion",
            "description": "Impossible de se connecter avec Google",
            "priority": "HIGH",
            "status": "TODO",
            "balise": "BUG"
            "assignee": 3
        }
    }
    ```
    tags:
      - Issues
    """
    serializer_class = IssueSerializer
    # L’utilisateur doit être authentifié et contributeur du projet
    permission_classes = [IsAuthenticated, IsContributor]

    def get_queryset(self):
        # Récupère toutes les issues liées au projet donné
        project_id = self.kwargs['project_id']
        return Issue.objects.filter(project__id=project_id)

    def get_serializer_context(self):
        # Passe l’objet projet et la requête au serializer
        context = super().get_serializer_context()
        project_id = self.kwargs['project_id']
        project = Project.objects.get(id=project_id)
        context['project'] = project
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        # Lors de la création, l’auteur est l’utilisateur connecté
        project = self.get_serializer_context()['project']
        serializer.save(author=self.request.user, project=project)

    def create(self, request, *args, **kwargs):
        # Personnalise la réponse avec un message clair
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    "message": f"L'issue '{serializer.data['title']}' a bien été créée.",
                    "issue": serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except serializers.ValidationError as e:
            return Response(
                {"message": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )


class IssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/projects/{project-id}/issues/{issue-id}/
    Récupère les détails d’une issue.

    PUT /api/projects/{project-id}/issues/{issue-id}/
    Met à jour une issue (réservé à l’auteur).

    DELETE /api/projects/{project-id}/issues/{issue-id}/
    Supprime une issue (réservé à l’auteur).

    ### Exemple de réponse à la mise à jour
    ```json
    {
        "message": "L'issue 'Bug de connexion' a été mise à jour.",
        "issue": {
            "id": 1,
            "title": "Bug corrigé",
            "status": "FINISHED"
        }
    }
    ```
    tags:
      - Issues
    """
    serializer_class = IssueSerializer
    # Seul l’auteur d’une issue peut la modifier ou supprimer
    permission_classes = [IsAuthenticated, IsAuthor]
    lookup_field = "project_id"
    lookup_url_kwargs = "issue_id"

    def get_queryset(self):
        # Retourne uniquement les issues du projet concerné
        project_id = self.kwargs['project_id']
        return Issue.objects.filter(project__id=project_id)

    def update(self, request, *args, **kwargs):
        # Mise à jour partielle d’une issue
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": f"L'issue '{serializer.data['title']}' a été mise à jour.",
            "issue": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        # Suppression d’une issue
        instance = self.get_object()
        title = instance.title
        self.perform_destroy(instance)
        return Response(
            {"message": f"L'issue '{title}' a été supprimée."},
            status=200
        )


class CommentListCreateView(generics.ListCreateAPIView):
    """
    GET /api/projects/{project-id}/issues/{issue-id}/comments/
    Récupère la liste des commentaires liés à une issue.

    POST /api/projects/{project-id}/issues/{issue-id}/comments/
    Crée un nouveau commentaire sur une issue.

    ### Exemple de corps de requête
    ```json
    {
        "description": "J’ai trouvé une solution temporaire."
    }
    ```

    ### Exemple de réponse
    ```json
    {
        "id": 1,
        "description": "J’ai trouvé une solution temporaire.",
        "created_time": "2025-09-20T10:00:00Z"
    }
    ```
    tags:
      - Issues
    """
    serializer_class = CommentSerializer
    # Seuls les contributeurs peuvent commenter
    permission_classes = [IsAuthenticated, IsContributor]
    lookup_url_kwarg = 'issue_id'

    def get_queryset(self):
        # Retourne les commentaires d’une issue spécifique
        issue_id = self.kwargs['issue_id']
        return Comment.objects.filter(issue__id=issue_id)

    def perform_create(self, serializer):
        # Lors de la création, on associe l’utilisateur et l’issue
        issue_id = self.kwargs['issue_id']
        issue = Issue.objects.get(id=issue_id)
        serializer.save(author=self.request.user, issue=issue)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/projects/{project-id}/issues/{issue-id}/comments/{comment-id}/
    Récupère un commentaire spécifique.

    PUT /api/projects/{project-id}/issues/{issue-id}/comments/{comment-id}/
    Met à jour un commentaire (réservé à l’auteur).

    DELETE /api/projects/{project-id}/issues/{issue-id}/comments/{comment-id}/
    Supprime un commentaire (réservé à l’auteur).

    tags:
      - Issues
    """
    serializer_class = CommentSerializer
    lookup_field = "issue_id"
    lookup_url_kwargs = "comment_id"
    # Seul l’auteur d’un commentaire peut le modifier ou le supprimer
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self):
        # On récupère les commentaires liés à l’issue concernée
        issue_id = self.kwargs['issue_id']
        return Comment.objects.filter(issue__id=issue_id)


class ContributorListCreateView(generics.ListCreateAPIView):
    """
    GET /api/projects/{project-id}/contributors/
    Liste les contributeurs du projet.

    POST /api/projects/{project-id}/contributors/
    Ajoute un contributeur au projet.

    ### Exemple de corps de requête
    ```json
    {
        "user": username,
    }
    ```

    ### Exemple de réponse
    ```json
    {
        "message": "Le contributeur 'username' a bien été ajouté à l'issue.",

    }
    ```
    tags:
      - Issues
    """
    serializer_class = ContributorSerializer
    # Seul l’auteur peut gérer les contributeurs
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self):
        # Retourne les contributeurs liés à un projet
        return Contributor.objects.filter(project_id=self.kwargs['project_pk'])

    def perform_create(self, serializer):
        # Ajout d’un contributeur à un projet
        project_id = self.kwargs['project_id']
        project = Project.objects.get(project_id=project_id)
        serializer.save(project=project)

    def get_serializer_context(self):
        # Passe l’objet projet au serializer
        context = super().get_serializer_context()
        project_id = self.kwargs['project_id']
        project = Project.objects.get(project_id=project_id)
        context['project'] = project
        return context

    def create(self, request, *args, **kwargs):
        # Réponse personnalisée après ajout d’un contributeur
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    "message": f"Le contributeur '{serializer.data['user']}' a bien été ajouté à l'issue.",
                    "contributor": serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except serializers.ValidationError as e:
            return Response(
                {"message": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )


class ContributorDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/projects/{project-id}/contributors/{id}/
    Supprime un contributeur d’un projet.

    ### Exemple de réponse
    ```json
    {
        "message": "Le contributeur 'user3' a été supprimé du projet."
    }
    ```
    tags:
      - Issues
    """
    serializer_class = ContributorSerializer
    # Seul l’auteur peut retirer un contributeur
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self):
        # Récupère les contributeurs liés au projet
        return Contributor.objects.filter(project_id=self.kwargs['project_pk'])

    def perform_destroy(self, instance):
        # L’auteur ne peut pas se retirer lui-même
        if instance.project.author == instance.user:
            raise ValidationError("Vous ne pouvez pas supprimer l'auteur du projet")
        instance.delete()
