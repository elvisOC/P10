from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Issue, Comment
from .serializers import IssueSerializer, CommentSerializer, ContributorSerializer
from .permissions import IsContributor, IsAuthor
from projects.models import Project


class IssuesListCreateView(generics.ListCreateAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated, IsContributor]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Issue.objects.filter(project__id=project_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        project_id = self.kwargs['project_id']
        project = Project.objects.get(id=project_id)
        context['project'] = project
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        project = self.get_serializer_context()['project']
        serializer.save(author=self.request.user, project=project)

    def create(self, request, *args, **kwargs):
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
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated, IsAuthor]
    lookup_field = "project_id"
    lookup_url_kwargs = "issue_id"

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Issue.objects.filter(project__id=project_id)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": f"L'issue '{serializer.data['title']}' a été mise à jour.",
            "issue": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        title = instance.title
        self.perform_destroy(instance)
        return Response(
            {"message": f"L'issue '{title}' a été supprimée."},
            status=200
        )


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsContributor]
    lookup_field = 'issue_id'
    lookup_url_kwarg = 'comment_id'

    def get_queryset(self):
        issue_id = self.kwargs['issue_id']
        return Comment.objects.filter(issue__id=issue_id)

    def perform_create(self, serializer):
        issue_id = self.kwargs['issue_id']
        issue = Issue.objects.get(id=issue_id)
        serializer.save(author=self.request.user, issue=issue)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self):
        issue_id = self.kwargs['issue_id']
        return Comment.objects.filter(issue__id=issue_id)


class ContributorListCreateView(generics.ListCreateAPIView):
    serializer_class = ContributorSerializer
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self):
        return Contributor.objects.filter(project_id=self.kwargs['project_pk'])

    def perform_create(self, serializer):
        project_id = self.kwargs['project_id']
        project = Project.objects.get(project_id=project_id)
        serializer.save(project=project)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        project_id = self.kwargs['project_id']
        project = Project.objects.get(project_id=project_id)
        context['project'] = project
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context=get_serializer_context())
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
    serializer_class = ContributorSerializer
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self):
        return Contributor.objects.filter(project_id=self.kwargs['project_pk'])

    def perform_destroy(self, instance):
        if instance.project.author == instance.user:
            raise ValidationError("Vous ne pouvez pas supprimer l'auteur du projet")
        instance.delete()
