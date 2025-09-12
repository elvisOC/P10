from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer, CustomUserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny


class SignupView(APIView):
    """
    POST /api/signup/

    Crée un nouvel utilisateur.

    Exemple de corps de requête :
    ```json
    {
        "username" : "username",
        "password" : "strong_password_123",
        "birth_date" : "YYYY-MM-DD",
        "can_be_contacted" : "yes",
        "can_data_be_shared" : "no"
    }
    ```

    Exemple de réponse : 
    ```json
    {
        "message": "Utilisateur crée avec succès"
    }
    ```
    """
    permission_classes = {AllowAny}
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Utilisateur crée avec succès"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserMeView(APIView):
    """
    GET /api/users/me/

    Exemple de réponse :
    ```json
    {
        "id": 1,
        "username": "username",
        "birth_date": "YYYY-MM-DD",
        "can_be_contacted": true,
        "can_data_be_shared": true
    }
    ```
    """

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)