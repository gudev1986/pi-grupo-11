from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('cadastrar/', views.cadastrar_usuario, name='cadastrar_usuario'),
]
