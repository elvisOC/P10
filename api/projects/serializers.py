from rest_framework import serializers
from .models import Project, Contributor
from rest_framework.exceptions import ValidationError
from issues.models import Issue
from django.contrib.auth import get_user_model

User = get_user_model()


# Serializer pour gérer les contributeurs
class ContributorSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username'
    )

    class Meta:
        model = Contributor
        fields = ['user']

    # Validation pour éviter les doublons
    def validate(self, data):
        user = data.get('user')
        project = data.get('project') or self.context.get('project')  # récupère le projet depuis le contexte si besoin

        # Vérifie que l'utilisateur n'est pas déjà contributeur du projet
        if Contributor.objects.filter(user=user, project=project).exists():
            raise serializers.ValidationError('Cet utilisateur est déjà contributeur de ce projet')

        data['project'] = project
        return data


# Serializer simple pour un projet (liste ou création)
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'type', 'created_time']
        read_only_fields = ['id', 'author', 'created_time']  # ces champs ne peuvent pas être modifiés par l'utilisateur

    def create(self, validated_data):
        # Crée le projet et ajoute automatiquement l'auteur comme contributeur
        project = Project.objects.create(**validated_data)
        Contributor.objects.create(user=project.author, project=project)
        return project


# Serializer imbriqué pour les issues liées à un projet
class NestedIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ['id', 'title']


# Serializer détaillé pour un projet (détails + contributeurs + issues)
class ProjectSerializerDetail(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(read_only=True, slug_field='username')
    contributors = ContributorSerializer(many=True, read_only=True)
    issues = NestedIssueSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'type', 'author', 'contributors', 'issues', 'created_time']
        read_only_fields = ['id', 'author', 'created_time']

    # Lors de la création, ajoute l'auteur comme contributeur
    def create(self, validated_data):
        project = Project.objects.create(**validated_data)
        Contributor.objects.create(user=project.author, project=project)
        return project
