from django.urls import path
from .views import SignupView, UserMeView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('users/me/', UserMeView.as_view(), name='user_me'),
]
