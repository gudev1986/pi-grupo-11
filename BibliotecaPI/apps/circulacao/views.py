from datetime import timedelta
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Min, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView

from apps.acervo.models import Exemplar
from apps.catalogo.models import Livro
from apps.usuarios.constants import ROLE_ADMIN
from apps.usuarios.permissions import AdminRequiredMixin
from apps.usuarios.utils import user_has_any_role

from .forms import DevolucaoForm, EmprestimoForm, ReservaForm
from .models import Emprestimo, Multa, Reserva
from .services import (
    PRAZO_EMPRESTIMO_DIAS,
    PRAZO_RESERVA_DIAS,
    atualizar_emprestimos_atrasados,
    criar_reserva_em_fila,
    criar_solicitacao_emprestimo,
    promover_reservas_da_fila,
    sincronizar_reservas_ativas,
)

User = get_user_model()


def _mensagem_validacao(exc):
    if hasattr(exc, 'message_dict'):
        for errors in exc.message_dict.values():
            if errors:
                return errors[0]
    if hasattr(exc, 'messages') and exc.messages:
        return exc.messages[0]
    return str(exc)


class EmprestimoListView(LoginRequiredMixin, ListView):
    model = Emprestimo
    template_name = 'circulacao/emprestimo_list.html'
    context_object_name = 'emprestimos'
    paginate_by = 20

    def get_queryset(self):
        atualizar_emprestimos_atrasados()
        sincronizar_reservas_ativas()

        queryset = Emprestimo.objects.select_related('exemplar__livro', 'usuario')
        if user_has_any_role(self.request.user, [ROLE_ADMIN]):
            q = self.request.GET.get('q')
            if q:
                queryset = queryset.filter(
                    Q(exemplar__livro__titulo__icontains=q)
                    | Q(exemplar__codigo_tombo__icontains=q)
                    | Q(usuario__username__icontains=q)
                )
            return queryset

        return queryset.filter(usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['is_admin_view'] = user_has_any_role(self.request.user, [ROLE_ADMIN])

        if not context['is_admin_view']:
            livros_com_solicitacao_ativa = set(
                Reserva.objects.filter(
                    usuario=self.request.user,
                    status=Reserva.Status.ATIVA,
                ).values_list('livro_id', flat=True)
            )
            context['livros_com_solicitacao_ativa'] = livros_com_solicitacao_ativa
            livros_disponiveis = (
                Livro.objects.select_related('categoria', 'editora')
                .prefetch_related('autores')
                .annotate(
                    exemplares_disponiveis=Count(
                        'exemplares',
                        filter=Q(exemplares__status=Exemplar.Status.DISPONIVEL),
                        distinct=True,
                    )
                )
                .filter(exemplares_disponiveis__gt=0)
            )

            if context['q']:
                livros_disponiveis = livros_disponiveis.filter(
                    Q(titulo__icontains=context['q'])
                    | Q(autores__nome__icontains=context['q'])
                    | Q(isbn_10__icontains=context['q'])
                    | Q(isbn_13__icontains=context['q'])
                )

            context['livros_disponiveis'] = livros_disponiveis.distinct().order_by('titulo')[:5]
            context['solicitacoes_retirada'] = (
                Reserva.objects.select_related('livro', 'exemplar')
                .filter(usuario=self.request.user, tipo=Reserva.Tipo.RETIRADA)
                .order_by('-data_reserva', '-id')
            )

        return context


class EmprestimoCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Emprestimo
    form_class = EmprestimoForm
    template_name = 'circulacao/emprestimo_form.html'
    success_url = reverse_lazy('circulacao:emprestimo_list')

    def dispatch(self, request, *args, **kwargs):
        sincronizar_reservas_ativas()
        self.reserva_origem = None
        reserva_id = request.GET.get('reserva') or request.POST.get('reserva')
        if reserva_id:
            self.reserva_origem = get_object_or_404(
                Reserva.objects.select_related('livro', 'usuario', 'exemplar'),
                pk=reserva_id,
                status=Reserva.Status.ATIVA,
            )
            if not self.reserva_origem.exemplar_id:
                messages.warning(request, 'A reserva ainda nao possui exemplar separado para retirada.')
                return redirect('circulacao:reserva_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['reserva'] = self.reserva_origem
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if self.reserva_origem:
            initial.update({
                'usuario': self.reserva_origem.usuario_id,
                'exemplar': self.reserva_origem.exemplar_id,
            })
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.reserva_origem:
            form.fields['usuario'].widget = forms.HiddenInput()
            form.fields['exemplar'].widget = forms.HiddenInput()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Novo emprestimo'
        context['prazo_dias'] = PRAZO_EMPRESTIMO_DIAS
        context['reserva_origem'] = self.reserva_origem
        context['cancel_url'] = self.request.GET.get('next') or reverse('circulacao:emprestimo_list')
        return context

    def get_success_url(self):
        return self.request.GET.get('next') or self.success_url

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        exemplar = self.object.exemplar
        exemplar.status = Exemplar.Status.EMPRESTADO
        exemplar.save(update_fields=['status'])

        if self.reserva_origem:
            self.reserva_origem.status = Reserva.Status.ATENDIDA
            self.reserva_origem.save(update_fields=['status'])

        devolucao = self.object.data_prevista_devolucao.strftime('%d/%m/%Y')
        messages.success(
            self.request,
            f'Emprestimo registrado. Devolucao prevista: {devolucao}.',
        )
        return response


class ReservaListView(LoginRequiredMixin, ListView):
    model = Reserva
    template_name = 'circulacao/reserva_list.html'
    context_object_name = 'reservas'

    def get_queryset(self):
        sincronizar_reservas_ativas()
        queryset = Reserva.objects.select_related('livro', 'usuario', 'exemplar').annotate(
            proxima_devolucao=Min(
                'livro__exemplares__emprestimos__data_prevista_devolucao',
                filter=Q(
                    livro__exemplares__emprestimos__status__in=[
                        Emprestimo.Status.ATIVO,
                        Emprestimo.Status.ATRASADO,
                    ]
                ),
            )
        )
        if user_has_any_role(self.request.user, [ROLE_ADMIN]):
            return queryset.filter(status=Reserva.Status.ATIVA).order_by('data_reserva', 'id')
        return queryset.filter(usuario=self.request.user).order_by('-data_reserva', '-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin_view'] = user_has_any_role(self.request.user, [ROLE_ADMIN])
        context['prazo_retirada_dias'] = PRAZO_RESERVA_DIAS

        if not context['is_admin_view']:
            context['livros_com_solicitacao_ativa'] = set(
                Reserva.objects.filter(
                    usuario=self.request.user,
                    status=Reserva.Status.ATIVA,
                ).values_list('livro_id', flat=True)
            )
            context['livros_indisponiveis'] = (
                Livro.objects.select_related('categoria', 'editora')
                .prefetch_related('autores')
                .annotate(
                    exemplares_disponiveis=Count(
                        'exemplares',
                        filter=Q(exemplares__status=Exemplar.Status.DISPONIVEL),
                        distinct=True,
                    ),
                    emprestimos_ativos=Count(
                        'exemplares__emprestimos',
                        filter=Q(
                            exemplares__emprestimos__status__in=[
                                Emprestimo.Status.ATIVO,
                                Emprestimo.Status.ATRASADO,
                            ]
                        ),
                        distinct=True,
                    ),
                    proxima_devolucao=Min(
                        'exemplares__emprestimos__data_prevista_devolucao',
                        filter=Q(
                            exemplares__emprestimos__status__in=[
                                Emprestimo.Status.ATIVO,
                                Emprestimo.Status.ATRASADO,
                            ]
                        ),
                    ),
                    fila_ativa=Count(
                        'reservas',
                        filter=Q(reservas__status=Reserva.Status.ATIVA),
                        distinct=True,
                    ),
                )
                .filter(exemplares_disponiveis=0, emprestimos_ativos__gt=0)
                .order_by('proxima_devolucao', 'titulo')
            )

        return context


class ReservaCreateView(LoginRequiredMixin, CreateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'circulacao/reserva_form.html'
    success_url = reverse_lazy('circulacao:reserva_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nova reserva'
        context['prazo_dias'] = PRAZO_RESERVA_DIAS
        return context

    def form_valid(self, form):
        livro = form.cleaned_data['livro']
        try:
            self.object = criar_reserva_em_fila(self.request.user, livro)
        except ValidationError as exc:
            form.add_error(None, _mensagem_validacao(exc))
            return self.form_invalid(form)

        messages.success(
            self.request,
            f'Reserva registrada com sucesso. Protocolo: {self.object.protocolo}.',
        )
        return redirect(self.get_success_url())


@login_required
@transaction.atomic
def registrar_devolucao(request, pk):
    if not user_has_any_role(request.user, [ROLE_ADMIN]):
        messages.error(request, 'Voce nao possui permissao para registrar devolucao.')
        return redirect('home')

    emprestimo = get_object_or_404(Emprestimo.objects.select_related('exemplar__livro', 'usuario'), pk=pk)
    if emprestimo.status == Emprestimo.Status.DEVOLVIDO:
        messages.warning(request, 'Este emprestimo ja foi devolvido.')
        return redirect('circulacao:emprestimo_list')

    if request.method == 'POST':
        data_devolucao = timezone.localdate()

        emprestimo.data_devolucao = data_devolucao
        emprestimo.status = Emprestimo.Status.DEVOLVIDO
        emprestimo.save(update_fields=['data_devolucao', 'status'])

        exemplar = emprestimo.exemplar
        exemplar.status = Exemplar.Status.DISPONIVEL
        exemplar.save(update_fields=['status'])
        promover_reservas_da_fila(exemplar.livro_id)

        dias_atraso = max((data_devolucao - emprestimo.data_prevista_devolucao).days, 0)
        if dias_atraso > 0:
            Multa.objects.get_or_create(
                emprestimo=emprestimo,
                defaults={
                    'valor': Decimal(dias_atraso) * Decimal('1.50'),
                    'motivo': f'Atraso de {dias_atraso} dia(s) na devolucao.',
                },
            )
            messages.warning(
                request,
                f'Devolucao registrada com {dias_atraso} dia(s) de atraso. Multa gerada.',
            )
        else:
            messages.success(request, 'Devolucao registrada com sucesso.')

        return redirect('circulacao:emprestimo_list')

    return render(request, 'circulacao/devolucao_form.html', {
        'emprestimo': emprestimo,
        'today': timezone.localdate(),
        'form': DevolucaoForm(),
    })


@login_required
@transaction.atomic
@require_POST
def renovar_emprestimo(request, pk):
    if not user_has_any_role(request.user, [ROLE_ADMIN]):
        messages.error(request, 'Voce nao possui permissao para renovar emprestimos.')
        return redirect('home')

    emprestimo = get_object_or_404(Emprestimo, pk=pk)
    if emprestimo.status == Emprestimo.Status.DEVOLVIDO:
        messages.warning(request, 'Emprestimos ja devolvidos nao podem ser renovados.')
        return redirect('circulacao:emprestimo_list')

    emprestimo.data_prevista_devolucao += timedelta(days=PRAZO_EMPRESTIMO_DIAS)
    if emprestimo.data_prevista_devolucao >= timezone.localdate():
        emprestimo.status = Emprestimo.Status.ATIVO
    emprestimo.save(update_fields=['data_prevista_devolucao', 'status'])

    nova_data = emprestimo.data_prevista_devolucao.strftime('%d/%m/%Y')
    messages.success(request, f'Emprestimo renovado. Nova devolucao prevista: {nova_data}.')
    return redirect('circulacao:emprestimo_list')


@login_required
@require_POST
def solicitar_reserva(request, livro_id):
    livro = get_object_or_404(Livro, pk=livro_id)
    try:
        reserva = criar_reserva_em_fila(request.user, livro)
    except ValidationError as exc:
        messages.error(request, _mensagem_validacao(exc))
    else:
        messages.success(
            request,
            f'Reserva criada. Protocolo para acompanhamento: {reserva.protocolo}.',
        )
    return redirect('circulacao:reserva_list')


@login_required
@require_POST
def solicitar_emprestimo(request, livro_id):
    livro = get_object_or_404(Livro, pk=livro_id)
    try:
        reserva = criar_solicitacao_emprestimo(request.user, livro)
    except ValidationError as exc:
        messages.error(request, _mensagem_validacao(exc))
    else:
        retirada = reserva.data_expiracao.strftime('%d/%m/%Y') if reserva.data_expiracao else '-'
        messages.success(
            request,
            f'Solicitacao registrada. Protocolo {reserva.protocolo}. Retire ate {retirada} no balcao.',
        )
    return redirect('circulacao:emprestimo_list')


@login_required
def api_buscar_livros(request):
    q = request.GET.get('q', '')
    livros = Livro.objects.filter(
        Q(titulo__icontains=q)
        | Q(autores__nome__icontains=q)
        | Q(isbn_10__icontains=q)
        | Q(isbn_13__icontains=q)
    ).distinct()[:20]

    results = [
        {
            'id': livro.id,
            'text': f"{livro.titulo} (ISBN: {livro.isbn_13 or livro.isbn_10 or '-'})",
        }
        for livro in livros
    ]
    return JsonResponse({'results': results})


@login_required
def api_buscar_exemplares(request):
    if not user_has_any_role(request.user, [ROLE_ADMIN]):
        return JsonResponse({'results': []})

    q = request.GET.get('q', '')
    exemplares = Exemplar.objects.filter(status=Exemplar.Status.DISPONIVEL)

    if q:
        exemplares = exemplares.filter(
            Q(livro__titulo__icontains=q)
            | Q(codigo_tombo__icontains=q)
        )

    exemplares = exemplares.select_related('livro')[:20]
    results = [
        {
            'id': ex.id,
            'text': f'Tombo: {ex.codigo_tombo} - {ex.livro.titulo}',
        }
        for ex in exemplares
    ]
    return JsonResponse({'results': results})


@login_required
def api_buscar_usuarios(request):
    if not user_has_any_role(request.user, [ROLE_ADMIN]):
        return JsonResponse({'results': []})

    q = request.GET.get('q', '')
    usuarios = User.objects.filter(
        Q(username__icontains=q)
        | Q(first_name__icontains=q)
        | Q(last_name__icontains=q)
        | Q(email__icontains=q)
    )[:20]

    results = [
        {
            'id': user.id,
            'text': f'{user.username} - {user.get_full_name()} ({user.email})',
        }
        for user in usuarios
    ]
    return JsonResponse({'results': results})
