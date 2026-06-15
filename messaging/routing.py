from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/mensajes/<int:conversation_id>/', consumers.ChatConsumer.as_asgi()),
    path('ws/notificaciones/', consumers.NotificationsConsumer.as_asgi()),
]
