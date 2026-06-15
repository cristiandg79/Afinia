from django.urls import path

from . import views

urlpatterns = [
    path('grupos/', views.group_list, name='group_list'),
    path('grupos/nuevo/', views.group_create, name='group_create'),
    path('grupos/<int:pk>/', views.group_detail, name='group_detail'),
    path('grupos/<int:pk>/unirse/', views.group_join, name='group_join'),
    path('grupos/<int:pk>/salir/', views.group_leave, name='group_leave'),
    path('grupos/<int:pk>/expulsar/<int:user_pk>/', views.group_remove_member, name='group_remove_member'),
    path('grupos/solicitud/<int:pk>/<str:status>/', views.group_membership_response, name='group_membership_response'),
    path('planes/', views.plan_list, name='plan_list'),
    path('planes/nuevo/', views.plan_create, name='plan_create'),
    path('planes/<int:pk>/', views.plan_detail, name='plan_detail'),
    path('planes/<int:pk>/unirse/', views.plan_join, name='plan_join'),
    path('planes/<int:pk>/salir/', views.plan_leave, name='plan_leave'),
    path('planes/<int:pk>/expulsar/<int:user_pk>/', views.plan_remove_attendee, name='plan_remove_attendee'),
    path('planes/solicitud/<int:pk>/<str:status>/', views.plan_attendance_response, name='plan_attendance_response'),
]
