from django.shortcuts import render

def chat_list(request):
    return render(request, 'chat/chat_list.html')  # Make sure this template exists

def chat_room(request, room_id):
    return render(request, 'chat/chat_room.html', {'room_id': room_id})
