from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="P10 API - Gestion de projets et tickets",
        default_version="v1",
        description=(
            "### Fonctionnalités principales :\n"
            "- Authentification JWT\n"
            "- Gestion des utilisateurs\n"
            "- Création et gestion des projets\n"
            "- Gestion des contributeurs\n"
            "- Création et suivi des issues\n"
            "- Ajout de commentaires sur les issues\n\n"
            "### Authentification :\n"
            "- Obtenir un token : **POST /api/token/**\n"
            "- Rafraîchir un token : **POST /api/token/refresh**\n\n"
            "### Endpoints principaux :\n"
            "- **/api/signup/** → Créer un utilisateur\n"
            "- **/api/projects/** → Lister & créer des projets\n"
            "- **/api/projects/<id>/** → Détails d’un projet\n"
            "- **/api/projects/<id>/contributors/** → Gérer les contributeurs\n"
            "- **/api/projects/<id>/issues/** → Gérer les issues d’un projet\n"
            "- **/api/projects/<id>/issues/<id>/comments/** → Gérer les commentaires"
        ),
        contact=openapi.Contact(email="elvis.degeitere1@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),

    #Auth JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    #Apps principales
    path('api/', include('users.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/', include('issues.urls')),

    #Documentation Swagger & Redoc
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
