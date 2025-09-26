from django.urls import path
from . import views

urlpatterns = [
    path('', views.IssuesListCreateView.as_view(), name='issues_list'),
    path('<int:issue_id>/', views.IssueDetailView.as_view(), name='issue_detail'),
    path('<int:issue_id>/comments/', views.CommentListCreateView.as_view(), name='comment_list'),
    path('<int:issue_id>/comments/<int:comment_id>/', views.CommentDetailView.as_view(), name='comment_detail'),
]
