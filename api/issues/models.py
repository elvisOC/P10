from django.db import models
from projects.models import Project
import uuid
from django.conf import settings


class Issue(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'Hight'),
    ]

    BALISE_CHOICES = [
        ('BUG', 'Bug'),
        ('FEATURE', 'Feature'),
        ('TASK', 'Task'),
    ]

    PROGRESS_CHOICES = [
        ('TODO', 'To do'),
        ('INPROGRESS', 'In progress'),
        ('FINISHED', 'Finish'),
    ]

    title = models.CharField(max_length=128)
    description = models.TextField()

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='issue'
    )

    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issues_assigned'
    )

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    balise = models.CharField(max_length=10, choices=BALISE_CHOICES)
    progress = models.CharField(max_length=10, choices=PROGRESS_CHOICES, default='TODO')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='issues')
    created_time = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comment')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_time = models.DateTimeField(auto_now_add=True)
