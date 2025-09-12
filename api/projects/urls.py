from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectDetailView,
    ContributorListCreateView,
    ContributorDeleteView
)

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project-list-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-view'),
    path('<int:project_pk>/contributors/', ContributorListCreateView.as_view(), name='contributor-list-create'),
    path('<int:project_pk>/contributors/<int:pk>/', ContributorDeleteView.as_view(), name='contributor-delete'),
]
