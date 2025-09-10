from rest_framework import serializers
from .models import Issue, Comment
from rest_framework.exceptions import ValidationError
from projects.models import Project, Contributor

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ['title', 'description', 'priority', 'balise', 'progress', 'project', 'created_time']
        read_only_fields = ['project', 'created_time']
        
        def create(self, validated_data):
            issue = Issue.objects.create(**validated_data)
            return issue
        
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['title', 'description']
        read_only_fields = ['issue', 'uuid', 'created_time', 'author']
        
        def create(self, validated_data):
            comment = Comment.objects.create(**validated_data)
            return comment