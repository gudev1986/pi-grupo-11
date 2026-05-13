from django.db import models
from apps.catalogo.models import Livro

class Exemplar(models.Model):

    class Status(models.TextChoices):
        DISPONIVEL = 'DISPONIVEL', 'Disponível'
        RESERVADO = 'RESERVADO', 'Reservado'
        EMPRESTADO = 'EMPRESTADO', 'Emprestado'

    livro = models.ForeignKey(
        Livro,
        on_delete=models.CASCADE,
        related_name='exemplares'
    )

    codigo_tombo = models.CharField(
        max_length=50,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISPONIVEL,
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.codigo_tombo
