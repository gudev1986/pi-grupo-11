from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.LivroListView.as_view(), name='livro_list'),
    path('livros/novo/', views.LivroCreateView.as_view(), name='livro_create'),
    path('livros/<int:pk>/', views.LivroDetailView.as_view(), name='livro_detail'),
    path('livros/<int:pk>/editar/', views.LivroUpdateView.as_view(), name='livro_update'),
    path('livros/<int:pk>/excluir/', views.LivroDeleteView.as_view(), name='livro_delete'),

    path('autores/', views.AutorListView.as_view(), name='autor_list'),
    path('autores/novo/', views.AutorCreateView.as_view(), name='autor_create'),
    path('autores/<int:pk>/editar/', views.AutorUpdateView.as_view(), name='autor_update'),
    path('autores/<int:pk>/excluir/', views.AutorDeleteView.as_view(), name='autor_delete'),

    path('editoras/', views.EditoraListView.as_view(), name='editora_list'),
    path('editoras/nova/', views.EditoraCreateView.as_view(), name='editora_create'),
    path('editoras/<int:pk>/editar/', views.EditoraUpdateView.as_view(), name='editora_update'),
    path('editoras/<int:pk>/excluir/', views.EditoraDeleteView.as_view(), name='editora_delete'),

    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/nova/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/excluir/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),
]
