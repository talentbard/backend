from django.db import models
from django.conf import settings


class Room(models.Model):
    # A chat room: could be group or direct (private)
    name = models.CharField(max_length=255, blank=True)
    is_group = models.BooleanField(default=True) 
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Room {self.id}"

class Message(models.Model):
    # A message in a room
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    # Delivery and read flags (could also use separate Receipt model for per-user tracking)
    delivered = models.BooleanField(default=False)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.room}] {self.sender}: {self.content[:20]}"

class UserStatus(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f"{self.user.username}: {status}"
