from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from core.models import PerfilUsuario

from .constants import ROLE_ADMIN
from .forms import UsuarioCadastroForm
from .utils import user_has_any_role


@login_required
def cadastrar_usuario(request):
    if not user_has_any_role(request.user, [ROLE_ADMIN]):
        messages.error(request, 'Você não possui permissão para cadastrar usuários.')
        return redirect('home')

    if request.method == 'POST':
        form = UsuarioCadastroForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    PerfilUsuario.objects.create(
                        user=user,
                        matricula=form.cleaned_data['matricula'],
                        precisa_trocar_senha=True,
                    )
            except IntegrityError:
                form.add_error('matricula', 'Já existe um usuário com esta matrícula.')
            else:
                messages.success(request, f'Usuário {user.username} cadastrado com sucesso.')
                return redirect('usuarios:cadastrar_usuario')
    else:
        form = UsuarioCadastroForm()

    return render(request, 'usuarios/cadastrar_usuario.html', {'form': form})
