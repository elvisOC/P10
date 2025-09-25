from rest_framework import serializers
from .models import Project, Contributor
from rest_framework.exceptions import ValidationError
from issues.models import Issue
from django.contrib.auth import get_user_model



User = get_user_model()
    
class ContributorSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),  
        slug_field='username'
    )

    class Meta:
        model = Contributor
        fields = ['user'] 

    def validate(self, data):
        user = data.get('user')
        project = data.get('project') or self.context.get('project')
        
        if Contributor.objects.filter(user=user, project=project).exists():
            raise serializers.ValidationError('Cet utilisateur est déjà contributeur de ce projet')
        
        data['project'] = project
        return data

        
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'type', 'created_time']
        read_only_fields = ['id', 'author', 'created_time']
        
    def create(self, validated_data):
        project = Project.objects.create(**validated_data)
        Contributor.objects.create(user=project.author, project=project)
        return project
    
    
class NestedIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ['id', 'title']
        
class ProjectSerializerDetail(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(read_only=True, slug_field='username')
    contributors = ContributorSerializer(many=True, read_only=True)
    issues = NestedIssueSerializer(many=True, read_only=True)
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'type', 'author', 'contributors', 'issues', 'created_time']
        read_only_fields = ['id', 'author', 'created_time']
        
    def create(self, validated_data):
        project = Project.objects.create(**validated_data)
        Contributor.objects.create(user=project.author, project=project, role='Author')
        return project