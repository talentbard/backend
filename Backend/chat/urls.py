from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),             # e.g. /chat/
    path('<int:room_id>/', views.chat_room, name='chat_room'),  # e.g. /chat/5/
]
