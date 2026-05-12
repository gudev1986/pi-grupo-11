from django.contrib import admin

from core.models import PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'matricula', 'precisa_trocar_senha')
    list_filter = ('precisa_trocar_senha',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'matricula')
    autocomplete_fields = ('user',)
    list_per_page = 25
