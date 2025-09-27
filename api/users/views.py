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

    ### Corps de requête (exemple)
    ```json
    {
        "username": "username",
        "password": "strong_password_123",
        "birth_date": "2000-01-01",
        "can_be_contacted": "yes",
        "can_data_be_shared": "no"
    }
    ```

    ### Réponses possibles
    - **201 CREATED**
    ```json
    {
        "message": "Utilisateur crée avec succès"
    }
    ```

    - **400 BAD REQUEST**
    ```json
    {
        "username": ["Ce nom d’utilisateur existe déjà."]
    }
    ```
    """
    # Endpoint public -> tout le monde peut s’inscrire 
    permission_classes = [AllowAny] 

    def post(self, request):
        # On sérialise les données envoyées dans la requête
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            # Si les données sont valides -> on crée l’utilisateur
            serializer.save()
            return Response(
                {"message": "Utilisateur crée avec succès"},
                status=status.HTTP_201_CREATED
            )
        # Sinon -> on renvoie les erreurs de validation
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserMeView(APIView):
    """
    Gestion du profil de l’utilisateur connecté.

    ### Endpoints disponibles :
    - **GET /api/me/** -> Récupère les informations de l’utilisateur connecté
    - **PUT /api/me/** -> Met à jour toutes les informations de l’utilisateur
    - **PATCH /api/me/** -> Met à jour partiellement les informations
    - **DELETE /api/me/** -> Supprime le compte utilisateur

    ---

    #### GET /api/me/
    **Réponse 200 OK**
    ```json
    {
        "id": 1,
        "username": "username",
        "birth_date": "2000-01-01",
        "can_be_contacted": "yes",
        "can_data_be_shared": "no"
    }
    ```

    #### PUT /api/me/
    **Corps de requête (exemple)**
    ```json
    {
        "username": "new_username",
        "birth_date": "1999-12-31",
        "can_be_contacted": "no",
        "can_data_be_shared": "yes"
    }
    ```

    **Réponse 200 OK**
    ```json
    {
        "id": 1,
        "username": "new_username",
        "birth_date": "1999-12-31",
        "can_be_contacted": "no",
        "can_data_be_shared": "yes"
    }
    ```

    #### PATCH /api/me/
    **Corps de requête (exemple)**
    ```json
    {
        "username": "patched_username"
    }
    ```

    **Réponse 200 OK**
    ```json
    {
        "id": 1,
        "username": "patched_username",
        "birth_date": "2000-01-01",
        "can_be_contacted": "yes",
        "can_data_be_shared": "no"
    }
    ```

    #### DELETE /api/me/
    **Réponse 200 OK**
    ```json
    {
        "message": "Utilisateur supprimé avec succès"
    }
    ```
    """
    # Ici -> seules les personnes authentifiées peuvent utiliser ces endpoints
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # On sérialise directement l’utilisateur connecté
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        # Mise à jour complète du profil (tous les champs doivent être envoyés)
        serializer = CustomUserSerializer(request.user, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()  # Enregistre les modifications
            return Response(serializer.data, status=status.HTTP_200_OK)
        # En cas d’erreurs de validation
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        # Mise à jour partielle (un ou plusieurs champs seulement)
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        # Suppression définitive du compte de l’utilisateur connecté
        user = request.user
        user.delete()
        return Response(
            {"message": "Utilisateur supprimé avec succès"},
            status=status.HTTP_200_OK
        )
