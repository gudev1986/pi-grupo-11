from django.contrib import admin
from .models import Autor, CapaLivro, Categoria, Editora, Livro


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    search_fields = ['nome']
    list_display = ['nome']


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ['nome']
    list_display = ['nome']


@admin.register(Editora)
class EditoraAdmin(admin.ModelAdmin):
    search_fields = ['nome']
    list_display = ['nome']


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'isbn_10', 'isbn_13', 'editora', 'ano_publicacao']
    search_fields = ['titulo', 'isbn_10', 'isbn_13']
    filter_horizontal = ['autores']


@admin.register(CapaLivro)
class CapaLivroAdmin(admin.ModelAdmin):
    list_display = ['livro', 'imagem', 'atualizado_em']
    search_fields = ['livro__titulo', 'livro__isbn_10', 'livro__isbn_13']
