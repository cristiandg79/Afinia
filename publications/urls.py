from django.urls import path

from . import views

urlpatterns = [
    path('', views.publication_feed, name='publication_feed'),
]
