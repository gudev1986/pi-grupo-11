from django.contrib.auth.models import Group

from .constants import ROLE_ADMIN, ROLE_LEITOR


def ensure_default_groups() -> None:
    for role in (ROLE_ADMIN, ROLE_LEITOR):
        Group.objects.get_or_create(name=role)


def user_has_any_role(user, roles) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=roles).exists()


def user_role_names(user):
    if not user.is_authenticated:
        return []
    if user.is_superuser:
        return [ROLE_ADMIN]
    return list(user.groups.values_list('name', flat=True))
