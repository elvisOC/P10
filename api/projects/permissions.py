from rest_framework.permissions import BasePermission
from .models import Project

class IsContributor(BasePermission):
    def has_object_permission(self, request, obj):
        return obj.contributors.filter(user=request.user).exists()

    
class IsAuthor(BasePermission):
    def has_object_permission(self, request, obj):
        return obj.author == request.user