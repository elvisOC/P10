from django.shortcuts import render
from rest_framework import generics, status
from .models import Project, Contributor
from .serializers import ProjectSerializer, ProjectSerializerDetail, ContributorSerializer
from .permissions import IsAuthor, IsContributor
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Project.objects.filter(contributors__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        
class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAuthor, IsContributor]
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsContributor()]
        elif self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated(), IsAuthor()]
        return super().get_permissions()
    
    def get_object(self, pk):
        return get_object_or_404(Project, pk=pk)
    
    def get(self, request, pk):
        project = self.get_object(pk)
        serializer = ProjectSerializerDetail(project)
        return Response(serializer.data)
    
    def put(self, request, pk):
        project = self.get_object(pk)
        serializer = ProjectSerializerDetail(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk):
        project = self.get_object(pk)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class ContributorListCreateView(generics.ListCreateAPIView):
    serializer_class = ContributorSerializer
    permission_classes = [IsAuthenticated, IsAuthor]
    
    def get_queryset(self):
        return Contributor.objects.filter(project_id=self.kwargs['project_pk'])
    
    def perform_create(self, serializer):
        project = Project.objects.get(pk=self.kwargs['project_pk'])
        serializer.save(project=project)
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = Project.objects.get(pk=self.kwargs['project_pk'])
        return context
    
    
class ContributorDeleteView(generics.DestroyAPIView):
    serializer_class = ContributorSerializer
    permission_classes = [IsAuthenticated, IsAuthor]
    
    def get_queryset(self):
        return Contributor.objects.filter(project_id=self.kwargs['project_pk'])
    
    def perform_destroy(self, instance):
        if instance.project.author == instance.user:
            raise ValidationError("Vous ne pouvez pas supprimer l'auteur du projet")
        instance.delete()