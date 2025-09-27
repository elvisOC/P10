from rest_framework.permissions import BasePermission
from .models import Project


class IsContributor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.contributors.filter(user=request.user).exists()


class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class IsAuthorOrContributor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or obj.contributors.filter(user=request.user).exists()


class IsProjectAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.project.author == request.user
