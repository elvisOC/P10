from rest_framework import serializers
from .models import CustomUser
from datetime import date


# Serializer pour l'inscription (création d'un nouvel utilisateur)
class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        # Champs demandés pour créer un utilisateur
        fields = ['username', 'password', 'birth_date', 'can_be_contacted', 'can_data_be_shared']
        # On empêche le mot de passe d'être renvoyé dans les réponses
        extra_kwargs = {'password': {'write_only': True}}

    # Vérifie que l'utilisateur a au moins 15 ans
    def validate_birth_date(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 15:
            raise serializers.ValidationError("L'utilisateur doit avoir plus de 15 ans")
        return value

    # On redéfinit la méthode create pour gérer le mot de passe correctement
    def create(self, validated_data):
        # On récupère et enlève le mot de passe du dictionnaire
        password = validated_data.pop('password')
        # On crée un utilisateur avec les autres infos
        user = CustomUser(**validated_data)
        # On utilise set_password pour chiffrer le mot de passe
        user.set_password(password)
        user.save()
        return user


# Serializer pour afficher et modifier les infos d'un utilisateur existant
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        # Champs visibles/modifiables
        fields = ['id', 'username', 'birth_date', 'can_be_contacted', 'can_data_be_shared']
        # L'ID est en lecture seule (non modifiable)
        read_only_fields = ['id']
