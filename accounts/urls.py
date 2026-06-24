from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('condiciones-privacidad/', views.legal_terms, name='legal_terms'),
    path('registro/', views.signup, name='signup'),
    path('panel/', views.dashboard, name='dashboard'),
    path('perfil/', views.my_profile, name='my_profile'),
    path('perfil/editar/', views.profile_edit, name='profile_edit'),
    path('perfil/eliminar/', views.profile_delete, name='profile_delete'),
    path('perfil/<str:username>/', views.profile_detail, name='profile_detail'),
    path('personas/', views.discover, name='discover'),
    path('contactos/', views.contacts, name='contacts'),
    path('contactos/<int:pk>/mensajes/', views.contact_conversation, name='contact_conversation'),
    path('pareja/', views.dating_search, name='dating_search'),
    path('pareja/<int:pk>/<str:action>/', views.dating_action, name='dating_action'),
    path('conexion/<int:pk>/solicitar/', views.request_connection, name='request_connection'),
    path('conexion/<int:pk>/<str:status>/', views.respond_connection, name='respond_connection'),
    path('contactos/<int:pk>/eliminar/', views.delete_contact, name='delete_contact'),
    path('contactos/<int:pk>/bloquear/', views.block_contact, name='block_contact'),
    path('contactos/<int:pk>/desbloquear/', views.unblock_contact, name='unblock_contact'),
    path('moderacion/', views.moderation_panel, name='moderation_panel'),
    path('moderacion/publicacion/<int:pk>/eliminar/', views.moderation_delete_publication, name='moderation_delete_publication'),
    path('moderacion/foto-publicacion/<int:pk>/eliminar/', views.moderation_delete_publication_photo, name='moderation_delete_publication_photo'),
    path('moderacion/comentario/<int:pk>/eliminar/', views.moderation_delete_publication_comment, name='moderation_delete_publication_comment'),
    path('moderacion/grupo/<int:pk>/eliminar/', views.moderation_delete_group, name='moderation_delete_group'),
    path('moderacion/plan/<int:pk>/eliminar/', views.moderation_delete_plan, name='moderation_delete_plan'),
    path('moderacion/mensaje/<int:pk>/eliminar/', views.moderation_delete_message, name='moderation_delete_message'),
    path('moderacion/foto-perfil/<int:pk>/eliminar/', views.moderation_delete_profile_photo, name='moderation_delete_profile_photo'),
    path('moderacion/foto-extra/<int:pk>/eliminar/', views.moderation_delete_extra_photo, name='moderation_delete_extra_photo'),
    path('moderacion/usuario/<int:pk>/bloquear/', views.moderation_block_user, name='moderation_block_user'),
]
