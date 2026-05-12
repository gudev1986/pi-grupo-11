from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Emprestimo(models.Model):
    class Status(models.TextChoices):
        ATIVO = 'ATIVO', 'Ativo'
        DEVOLVIDO = 'DEVOLVIDO', 'Devolvido'
        ATRASADO = 'ATRASADO', 'Atrasado'

    exemplar = models.ForeignKey('acervo.Exemplar', on_delete=models.PROTECT, related_name='emprestimos', verbose_name='Exemplar')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='emprestimos', verbose_name='Usuário')
    data_emprestimo = models.DateField(auto_now_add=True, verbose_name='Data do empréstimo')
    data_prevista_devolucao = models.DateField(verbose_name='Data prevista de devolução')
    data_devolucao = models.DateField(null=True, blank=True, verbose_name='Data de devolução')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ATIVO, db_index=True, verbose_name='Situação')

    class Meta:
        ordering = ['-data_emprestimo']
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'
        constraints = [
            models.UniqueConstraint(
                fields=['exemplar'],
                condition=Q(status='ATIVO'),
                name='unique_emprestimo_ativo_por_exemplar',
            )
        ]

    def __str__(self):
        return f'Empréstimo {self.id} - {self.exemplar.codigo_tombo}'

    def clean(self):
        if not self.pk and self.exemplar_id and self.exemplar.status != 'DISPONIVEL':
            raise ValidationError({'exemplar': 'Exemplar indisponível para empréstimo.'})
        if self.data_devolucao and self.data_emprestimo and self.data_devolucao < self.data_emprestimo:
            raise ValidationError({'data_devolucao': 'A data de devolução não pode ser anterior ao empréstimo.'})

    def atualizar_status_atraso(self):
        if self.status == self.Status.ATIVO and self.data_prevista_devolucao < timezone.localdate():
            self.status = self.Status.ATRASADO


class Reserva(models.Model):
    class Status(models.TextChoices):
        ATIVA = 'ATIVA', 'Ativa'
        ATENDIDA = 'ATENDIDA', 'Atendida'
        CANCELADA = 'CANCELADA', 'Cancelada'
        EXPIRADA = 'EXPIRADA', 'Expirada'

    livro = models.ForeignKey('catalogo.Livro', on_delete=models.CASCADE, related_name='reservas', verbose_name='Livro')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas', verbose_name='Usuário')
    data_reserva = models.DateField(auto_now_add=True, verbose_name='Data da reserva')
    data_expiracao = models.DateField(null=True, blank=True, verbose_name='Data de expiração')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ATIVA, db_index=True, verbose_name='Situação')

    class Meta:
        ordering = ['-data_reserva']
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f'Reserva {self.id} - {self.livro.titulo}'


class Multa(models.Model):
    class StatusPagamento(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        PAGO = 'PAGO', 'Pago'

    emprestimo = models.OneToOneField(Emprestimo, on_delete=models.CASCADE, related_name='multa', verbose_name='Empréstimo')
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='Valor')
    motivo = models.CharField(max_length=255, verbose_name='Motivo')
    status_pagamento = models.CharField(
        max_length=10,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE,
        verbose_name='Situação do pagamento',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Multa'
        verbose_name_plural = 'Multas'

    def __str__(self):
        return f'Multa {self.id} - R$ {self.valor}'
