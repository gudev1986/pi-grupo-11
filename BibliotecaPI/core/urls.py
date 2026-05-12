from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('trocar-senha/', views.trocar_senha, name='trocar_senha'),
]
