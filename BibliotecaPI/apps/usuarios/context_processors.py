from .constants import ROLE_ADMIN
from .utils import user_has_any_role, user_role_names


def user_roles(request):
    user = request.user
    return {
        'user_role_names': user_role_names(user),
        'is_admin': user_has_any_role(user, [ROLE_ADMIN]),
        # Alias mantido para templates existentes não quebrarem
        'is_admin_or_bibliotecario': user_has_any_role(user, [ROLE_ADMIN]),
    }
