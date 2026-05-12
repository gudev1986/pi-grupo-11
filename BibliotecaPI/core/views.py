from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render

from apps.acervo.models import Exemplar
from apps.catalogo.models import Livro
from apps.circulacao.models import Emprestimo

from .models import PerfilUsuario


def _apply_bootstrap(form):
    for field in form.fields.values():
        field.widget.attrs.setdefault('class', 'form-control')


@login_required
def home(request):
    try:
        if request.user.perfilusuario.precisa_trocar_senha:
            return redirect('trocar_senha')
    except PerfilUsuario.DoesNotExist:
        pass

    context = {
        'total_livros_catalogo': Livro.objects.count(),
        'total_exemplares_disponiveis': Exemplar.objects.filter(status=Exemplar.Status.DISPONIVEL).count(),
        'total_emprestimos_ativos': Emprestimo.objects.filter(status=Emprestimo.Status.ATIVO).count(),
    }
    return render(request, 'core/home.html', context)


@login_required
def trocar_senha(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        _apply_bootstrap(form)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            try:
                perfil = user.perfilusuario
                perfil.precisa_trocar_senha = False
                perfil.save(update_fields=['precisa_trocar_senha'])
            except PerfilUsuario.DoesNotExist:
                pass
            messages.success(request, 'Senha atualizada com sucesso.')
            return redirect('home')
        messages.error(request, 'Corrija os erros para continuar.')
    else:
        form = PasswordChangeForm(request.user)
        _apply_bootstrap(form)

    return render(request, 'core/trocar_senha.html', {'form': form})
