from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Message, ChatRoom, UserProfile
from .serializers import MessageSerializer, ChatRoomSerializer, UserProfileSerializer
from django.contrib.auth import get_user_model

class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MessageSerializer
    def get_queryset(self):
        room_id = self.request.query_params.get('room')
        if room_id:
            return Message.objects.filter(room_id=room_id).order_by('timestamp')
        return Message.objects.none()
