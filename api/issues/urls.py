from django.urls import path
from . import views

urlpatterns = [
    path('projects/<int:project_id>/issues/', views.IssuesListCreateView.as_view(), name='issues-list'),
    path('projects/<int:project_id>/issues/<int:pk>/', views.IssueDetailView.as_view(), name='issue-detail'),
    path('projects/<int:project_id>/issues/<int:issue_id>/comments/', views.CommentListCreateView.as_view(), name='comment-list'),
    path('projects/<int:project_id>/issues/<int:issue_id>/comments/<int:comment_id>/', views.CommentDetailView.as_view(), name='comment-detail'),
]
