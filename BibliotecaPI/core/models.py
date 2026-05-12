from django.contrib.auth.models import User
from django.db import models


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Usuário')
    matricula = models.CharField(max_length=20, unique=True, verbose_name='Matrícula')
    precisa_trocar_senha = models.BooleanField(default=True, verbose_name='Precisa trocar senha')

    class Meta:
        verbose_name = 'Perfil de usuário'
        verbose_name_plural = 'Perfis de usuários'

    def __str__(self):
        return f'{self.user.username} - {self.matricula}'
