from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect

from .constants import ROLE_ADMIN
from .utils import user_has_any_role


class AdminRequiredMixin(AccessMixin):
    """Permite acesso apenas a administradores (e superusuários)."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not user_has_any_role(request.user, [ROLE_ADMIN]):
            messages.error(request, 'Você não possui permissão para acessar esta área.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


# Mantido como alias para não quebrar imports existentes durante migração
AdminOrBibliotecarioRequiredMixin = AdminRequiredMixin
