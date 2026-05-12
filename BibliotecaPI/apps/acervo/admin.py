from django.contrib import admin
from .models import Exemplar


@admin.register(Exemplar)
class ExemplarAdmin(admin.ModelAdmin):
    list_display = ['codigo_tombo', 'livro', 'status']
    search_fields = ['codigo_tombo', 'livro__titulo']
    list_filter = ['status']