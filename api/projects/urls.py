from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectDetailView,
    ContributorListCreateView,
    ContributorDeleteView
)

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project_list_create'),
    path('<int:project_id>/', ProjectDetailView.as_view(), name='project_view'),
    path('<int:project_id>/contributors/', ContributorListCreateView.as_view(), name='contributor_list_create'),
    path('<int:project_id>/contributors/<int:id>/', ContributorDeleteView.as_view(), name='contributor_delete'),
]
