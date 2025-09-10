from django.shortcuts import render
from rest_framework import generics
from .models import Issue, Comment
from .serializers import IssueSerializer, CommentSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .permissions import IsContributor, IsAuthor
from projects.models import Project

class IssuesListCreateView(generics.ListCreateAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated, IsContributor]
    
    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Issue.objects.filter(project__id=project_id)
    
    def perform_create(self, serializer):
        project = Project.objects.get(id=self.kwargs['project_id'])
        serializer.save(author=self.request.user, project=project)
        
class IssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated, IsAuthor]
    
    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Issue.objects.filter(project__id=project_id)
    
class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsContributor]
    
    def get_queryset(self):
        issue_id = self.kwargs['issue_id']
        return Comment.objects.filter(issue__id=issue_id)
    
    def perform_create(self, serializer):
        issue_id = self.kwargs['issue_id']
        serializer.save(author=self.request.user, issue_id=issue_id)
        
class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAuthor]
    def get_queryset(self):
        issues_id = self.kwargs['issue_id']
        return Comment.objects.filter(issues__id=issues_id)
    

