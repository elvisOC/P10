from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Issue, Comment
from projects.models import Project, Contributor

User = get_user_model()


class IssueSerializer(serializers.ModelSerializer):
    assignee = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Issue
        fields = [
            'id', 'title', 'description', 'priority', 
            'balise', 'progress', 'assignee', 'project', 'created_time'
        ]
        read_only_fields = ['id', 'created_time', 'project']


    def validate_assignee(self, value):
        project = self.context.get('project')
        if value and not project.contributors.filter(user=value).exists() and project.author != value:
            raise serializers.ValidationError(f"{value.username} n'est pas contributeur de ce projet")
        return value


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['title', 'description']
        read_only_fields = ['issue', 'uuid', 'created_time', 'author']


    def create(self, validated_data):
        comment = Comment.objects.create(**validated_data)
        return comment


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
        project = self.context.get('project')
        if Contributor.objects.filter(user=user, project=project).exists():
            raise serializers.ValidationError('Cet utilisateur est déjà contributeur de ce projet')
        return data
