from rest_framework import serializers
from .models import CustomUser
from datetime import date

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'birth_date', 'can_be_contacted', 'can_data_be_shared']
        extra_kwargs = {'password': {'write_only': True}}
        
    def validate_birth_date(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 15:
            raise serializers.ValidationError("L'utilisateur doit avoir plus de 15 ans")
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user
        
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'birth_date', 'can_be_contacted', 'can_data_be_shared']
        read_only_fields = ['id', 'username']