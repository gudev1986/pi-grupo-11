from django.urls import path

from . import views

app_name = 'acervo'

urlpatterns = [
    path('exemplares/', views.ExemplarListView.as_view(), name='exemplar_list'),
    path('exemplares/novo/', views.ExemplarCreateView.as_view(), name='exemplar_create'),
    path('exemplares/<int:pk>/editar/', views.ExemplarUpdateView.as_view(), name='exemplar_update'),
    path('exemplares/<int:pk>/excluir/', views.ExemplarDeleteView.as_view(), name='exemplar_delete'),
]
