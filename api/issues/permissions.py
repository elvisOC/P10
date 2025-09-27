from rest_framework.permissions import BasePermission
from projects.models import Contributor, Project


class IsContributor(BasePermission):
    def has_object_permission(self, request, view, obj):
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False
        return Contributor.objects.filter(project__id=project_id, user=request.user).exists()


class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
