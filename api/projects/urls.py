from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectDetailView,
    ContributorView
)

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project_list_create'),
    path('<int:project_id>/', ProjectDetailView.as_view(), name='project_view'),
    path('<int:project_id>/contributors/', ContributorView.as_view(), name='contributor_list_create'),
]
