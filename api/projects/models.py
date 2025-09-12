from django.db import models
from django.conf import settings

class Project(models.Model):
    TYPE_CHOICES = [
        ('BACKEND', 'Back-end'),
        ('FRONTEND', 'Front-end'),
        ('IOS', 'iOS'),
        ('ANDROID', 'Android'),
    ]
    
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=128)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='projects'
    )
    created_time = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
class Contributor(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='contributors'
    )
        
    class Meta:
        unique_together = ('user', 'project')
