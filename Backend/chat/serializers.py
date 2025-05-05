from rest_framework import serializers
from .models import Message, ChatRoom, UserProfile
from django.contrib.auth import get_user_model
from django.utils import timezone


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'content', 'timestamp', 'read', 'delivered']
