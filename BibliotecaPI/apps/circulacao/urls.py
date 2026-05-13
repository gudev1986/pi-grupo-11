from django.urls import path

from . import views

app_name = 'circulacao'

urlpatterns = [
    path('emprestimos/', views.EmprestimoListView.as_view(), name='emprestimo_list'),
    path('emprestimos/novo/', views.EmprestimoCreateView.as_view(), name='emprestimo_create'),
    path('emprestimos/<int:pk>/devolver/', views.registrar_devolucao, name='registrar_devolucao'),
    path('emprestimos/<int:pk>/renovar/', views.renovar_emprestimo, name='renovar_emprestimo'),
    path('reservas/', views.ReservaListView.as_view(), name='reserva_list'),
    path('reservas/nova/', views.ReservaCreateView.as_view(), name='reserva_create'),

    # Endpoints de API para as buscas dinâmicas
    path('api/livros/', views.api_buscar_livros, name='api_buscar_livros'),
    path('api/exemplares/', views.api_buscar_exemplares, name='api_buscar_exemplares'),
    path('api/usuarios/', views.api_buscar_usuarios, name='api_buscar_usuarios'),
]
