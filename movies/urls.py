from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('grossing/', views.grossing, name='grossing'),
    path('analytics/', views.analytics, name='analytics'),
]