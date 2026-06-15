from django.urls import path

from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('chat/', views.chat_lobby, name='chat_lobby'),
    path('chat/<slug:slug>/', views.chat_room_enter, name='chat_room_enter'),
    path('eliminar/', views.delete_conversations, name='delete_conversations'),
    path('<int:pk>/fila/', views.conversation_row, name='conversation_row'),
    path('<int:pk>/eliminar/', views.delete_conversation, name='delete_conversation'),
    path('<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('mensaje/<int:pk>/editar/', views.message_edit, name='message_edit'),
    path('mensaje/<int:pk>/eliminar/', views.message_delete, name='message_delete'),
]
