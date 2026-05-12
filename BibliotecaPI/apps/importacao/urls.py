from django.urls import path
from .views import importar_csv, download_template_csv

app_name = 'importacao'

urlpatterns = [
    path('', importar_csv, name='importar_csv'),
    path('template/', download_template_csv, name='template_csv'),
]
