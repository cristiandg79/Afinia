from django.urls import path

from . import views

urlpatterns = [
    path('', views.publication_feed, name='publication_feed'),
    path('<int:pk>/like/', views.publication_like, name='publication_like'),
    path('<int:pk>/comentar/', views.publication_comment, name='publication_comment'),
]
