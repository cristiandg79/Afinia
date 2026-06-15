from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('registro/', views.signup, name='signup'),
    path('panel/', views.dashboard, name='dashboard'),
    path('perfil/', views.my_profile, name='my_profile'),
    path('perfil/editar/', views.profile_edit, name='profile_edit'),
    path('perfil/eliminar/', views.profile_delete, name='profile_delete'),
    path('perfil/<int:pk>/', views.profile_detail, name='profile_detail'),
    path('personas/', views.discover, name='discover'),
    path('contactos/', views.contacts, name='contacts'),
    path('pareja/', views.dating_search, name='dating_search'),
    path('pareja/<int:pk>/<str:action>/', views.dating_action, name='dating_action'),
    path('conexion/<int:pk>/solicitar/', views.request_connection, name='request_connection'),
    path('conexion/<int:pk>/<str:status>/', views.respond_connection, name='respond_connection'),
    path('contactos/<int:pk>/bloquear/', views.block_contact, name='block_contact'),
    path('contactos/<int:pk>/desbloquear/', views.unblock_contact, name='unblock_contact'),
]
