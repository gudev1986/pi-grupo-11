from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


class Autor(models.Model):
    nome = models.CharField(max_length=180, unique=True)

    def __str__(self):
        return self.nome


class Editora(models.Model):
    nome = models.CharField(max_length=180, unique=True)

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    nome = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.nome


class Livro(models.Model):
    titulo = models.CharField(max_length=220)

    isbn_10 = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True,
    )

    isbn_13 = models.CharField(
        max_length=13,
        unique=True,
        blank=True,
        null=True,
    )

    autores = models.ManyToManyField(
        Autor,
        related_name='livros'
    )

    editora = models.ForeignKey(
        Editora,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    ano_publicacao = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['titulo']

    def __str__(self):
        return self.titulo
