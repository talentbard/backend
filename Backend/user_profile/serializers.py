from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'email_id', 'phone_no', 'password','role','designation']


class UserLoginSerializer(serializers.Serializer):
    email_id = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField()


class TokenRefreshSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    refresh_token = serializers.CharField()
