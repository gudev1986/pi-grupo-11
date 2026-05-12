from django.contrib import admin
from .models import Autor, Categoria, Editora, Livro


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
