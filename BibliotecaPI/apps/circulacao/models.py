from decimal import Decimal
from uuid import uuid4

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
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='emprestimos', verbose_name='Usuario')
    data_emprestimo = models.DateField(auto_now_add=True, verbose_name='Data do emprestimo')
    data_prevista_devolucao = models.DateField(verbose_name='Data prevista de devolucao')
    data_devolucao = models.DateField(null=True, blank=True, verbose_name='Data de devolucao')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ATIVO, db_index=True, verbose_name='Situacao')

    class Meta:
        ordering = ['-data_emprestimo']
        verbose_name = 'Emprestimo'
        verbose_name_plural = 'Emprestimos'
        constraints = [
            models.UniqueConstraint(
                fields=['exemplar'],
                condition=Q(status='ATIVO'),
                name='unique_emprestimo_ativo_por_exemplar',
            )
        ]

    def __str__(self):
        return f'Emprestimo {self.id} - {self.exemplar.codigo_tombo}'

    def clean(self):
        if not self.pk and self.exemplar_id and self.exemplar.status not in {'DISPONIVEL', 'RESERVADO'}:
            raise ValidationError({'exemplar': 'Exemplar indisponivel para emprestimo.'})
        if self.data_devolucao and self.data_emprestimo and self.data_devolucao < self.data_emprestimo:
            raise ValidationError({'data_devolucao': 'A data de devolucao nao pode ser anterior ao emprestimo.'})

    def atualizar_status_atraso(self):
        if self.status == self.Status.ATIVO and self.data_prevista_devolucao < timezone.localdate():
            self.status = self.Status.ATRASADO


class Reserva(models.Model):
    class Status(models.TextChoices):
        ATIVA = 'ATIVA', 'Ativa'
        ATENDIDA = 'ATENDIDA', 'Atendida'
        CANCELADA = 'CANCELADA', 'Cancelada'
        EXPIRADA = 'EXPIRADA', 'Expirada'

    class Tipo(models.TextChoices):
        FILA = 'FILA', 'Fila de espera'
        RETIRADA = 'RETIRADA', 'Retirada no balcao'

    livro = models.ForeignKey('catalogo.Livro', on_delete=models.CASCADE, related_name='reservas', verbose_name='Livro')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas', verbose_name='Usuario')
    exemplar = models.ForeignKey(
        'acervo.Exemplar',
        on_delete=models.SET_NULL,
        related_name='reservas',
        null=True,
        blank=True,
        verbose_name='Exemplar separado',
    )
    protocolo = models.CharField(max_length=24, unique=True, null=True, blank=True, verbose_name='Protocolo')
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.FILA, db_index=True, verbose_name='Tipo')
    data_reserva = models.DateField(auto_now_add=True, verbose_name='Data da reserva')
    data_expiracao = models.DateField(null=True, blank=True, verbose_name='Data de expiracao')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ATIVA, db_index=True, verbose_name='Situacao')

    class Meta:
        ordering = ['data_reserva', 'id']
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        constraints = [
            models.UniqueConstraint(
                fields=['livro', 'usuario'],
                condition=Q(status='ATIVA'),
                name='unique_reserva_ativa_por_livro_usuario',
            )
        ]

    def __str__(self):
        return f'Reserva {self.protocolo or self.id} - {self.livro.titulo}'

    def clean(self):
        if self.exemplar_id and self.exemplar.livro_id != self.livro_id:
            raise ValidationError({'exemplar': 'O exemplar precisa pertencer ao livro reservado.'})

    def save(self, *args, **kwargs):
        if not self.protocolo:
            self.protocolo = self.gerar_protocolo()
        super().save(*args, **kwargs)

    @classmethod
    def gerar_protocolo(cls):
        while True:
            protocolo = f'RSV-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}'
            if not cls.objects.filter(protocolo=protocolo).exists():
                return protocolo

    @property
    def pronta_para_retirada(self):
        return self.status == self.Status.ATIVA and self.exemplar_id is not None


class Multa(models.Model):
    class StatusPagamento(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        PAGO = 'PAGO', 'Pago'

    emprestimo = models.OneToOneField(Emprestimo, on_delete=models.CASCADE, related_name='multa', verbose_name='Emprestimo')
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='Valor')
    motivo = models.CharField(max_length=255, verbose_name='Motivo')
    status_pagamento = models.CharField(
        max_length=10,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE,
        verbose_name='Situacao do pagamento',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Multa'
        verbose_name_plural = 'Multas'

    def __str__(self):
        return f'Multa {self.id} - R$ {self.valor}'
