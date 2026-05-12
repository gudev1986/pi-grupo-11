from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from core.models import PerfilUsuario


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_redirect_to_password_change(request):
            return redirect('trocar_senha')
        return self.get_response(request)

    def _should_redirect_to_password_change(self, request) -> bool:
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False

        allowed_paths = {
            reverse('trocar_senha'),
            reverse('logout'),
        }
        if request.path in allowed_paths:
            return False
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return False

        try:
            return user.perfilusuario.precisa_trocar_senha
        except PerfilUsuario.DoesNotExist:
            return False
