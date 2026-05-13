from pathlib import Path

from django.db import models
from django.utils.text import slugify


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

    @property
    def capa_imagem(self):
        if hasattr(self, 'capa') and self.capa.imagem:
            return self.capa.imagem
        return None

    def __str__(self):
        return self.titulo


def capa_livro_upload_to(instance, filename):
    extensao = Path(filename).suffix.lower()
    nome_base = slugify(instance.livro.titulo) or f'livro-{instance.livro_id}'
    return f'capas/livro_{instance.livro_id}/{nome_base}{extensao}'


class CapaLivro(models.Model):
    livro = models.OneToOneField(
        Livro,
        on_delete=models.CASCADE,
        related_name='capa',
    )
    imagem = models.ImageField(upload_to=capa_livro_upload_to)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'capa de livro'
        verbose_name_plural = 'capas de livros'

    def save(self, *args, **kwargs):
        imagem_anterior = None
        if self.pk:
            imagem_anterior = type(self).objects.filter(pk=self.pk).values_list('imagem', flat=True).first()
        super().save(*args, **kwargs)
        if imagem_anterior and imagem_anterior != self.imagem.name:
            self.imagem.storage.delete(imagem_anterior)

    def delete(self, *args, **kwargs):
        imagem = self.imagem
        super().delete(*args, **kwargs)
        if imagem:
            imagem.delete(save=False)

    def __str__(self):
        return f'Capa de {self.livro}'
