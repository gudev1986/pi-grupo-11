from django.contrib import admin

from .models import Emprestimo, Multa, Reserva


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ('id', 'exemplar', 'usuario', 'data_emprestimo', 'data_prevista_devolucao', 'data_devolucao', 'status')
    list_filter = ('status', 'data_emprestimo', 'data_prevista_devolucao')
    search_fields = ('=id', 'usuario__username', 'exemplar__codigo_tombo', 'exemplar__livro__titulo')
    autocomplete_fields = ('exemplar', 'usuario')
    date_hierarchy = 'data_emprestimo'
    list_per_page = 25


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'livro', 'usuario', 'data_reserva', 'data_expiracao', 'status')
    list_filter = ('status', 'data_reserva')
    search_fields = ('livro__titulo', 'usuario__username')
    autocomplete_fields = ('livro', 'usuario')
    date_hierarchy = 'data_reserva'
    list_per_page = 25


@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ('id', 'emprestimo', 'valor', 'motivo', 'status_pagamento')
    list_filter = ('status_pagamento',)
    search_fields = ('=emprestimo__id', 'motivo', 'emprestimo__usuario__username')
    autocomplete_fields = ('emprestimo',)
    list_per_page = 25