from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usuarios'
    verbose_name = 'Usuários'

    def ready(self):
        from django.db.models.signals import post_migrate

        post_migrate.connect(create_default_groups, sender=self, dispatch_uid='usuarios_create_default_groups')


def create_default_groups(sender, **kwargs):
    from .utils import ensure_default_groups

    ensure_default_groups()
