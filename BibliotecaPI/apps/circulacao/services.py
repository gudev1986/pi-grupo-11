from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.acervo.models import Exemplar

from .models import Emprestimo, Reserva

PRAZO_RESERVA_DIAS = 3
PRAZO_EMPRESTIMO_DIAS = 7


def atualizar_emprestimos_atrasados():
    Emprestimo.objects.filter(
        status=Emprestimo.Status.ATIVO,
        data_prevista_devolucao__lt=timezone.localdate(),
    ).update(status=Emprestimo.Status.ATRASADO)


def expirar_reservas_vencidas():
    hoje = timezone.localdate()
    reservas_expiradas = list(
        Reserva.objects.select_related('exemplar')
        .filter(
            status=Reserva.Status.ATIVA,
            exemplar__isnull=False,
            data_expiracao__lt=hoje,
        )
    )

    livros_afetados = set()
    for reserva in reservas_expiradas:
        exemplar = reserva.exemplar
        if exemplar and exemplar.status == Exemplar.Status.RESERVADO:
            exemplar.status = Exemplar.Status.DISPONIVEL
            exemplar.save(update_fields=['status'])
            livros_afetados.add(reserva.livro_id)

        reserva.status = Reserva.Status.EXPIRADA
        reserva.exemplar = None
        reserva.save(update_fields=['status', 'exemplar'])

    for livro_id in livros_afetados:
        promover_reservas_da_fila(livro_id)


def promover_reservas_da_fila(livro_id):
    hoje = timezone.localdate()
    reservas_pendentes = list(
        Reserva.objects.filter(
            livro_id=livro_id,
            status=Reserva.Status.ATIVA,
            tipo=Reserva.Tipo.FILA,
            exemplar__isnull=True,
        )
        .order_by('data_reserva', 'id')
    )
    exemplares_disponiveis = list(
        Exemplar.objects.filter(
            livro_id=livro_id,
            status=Exemplar.Status.DISPONIVEL,
        ).order_by('codigo_tombo')
    )

    for reserva, exemplar in zip(reservas_pendentes, exemplares_disponiveis):
        exemplar.status = Exemplar.Status.RESERVADO
        exemplar.save(update_fields=['status'])

        reserva.exemplar = exemplar
        reserva.data_expiracao = hoje + timedelta(days=PRAZO_RESERVA_DIAS)
        reserva.save(update_fields=['exemplar', 'data_expiracao'])


def sincronizar_reservas_ativas():
    expirar_reservas_vencidas()
    livros_ids = (
        Reserva.objects.filter(
            status=Reserva.Status.ATIVA,
            tipo=Reserva.Tipo.FILA,
            exemplar__isnull=True,
        )
        .values_list('livro_id', flat=True)
        .distinct()
    )
    for livro_id in livros_ids:
        promover_reservas_da_fila(livro_id)


def validar_reserva_ativa(usuario, livro):
    if Reserva.objects.filter(usuario=usuario, livro=livro, status=Reserva.Status.ATIVA).exists():
        raise ValidationError('Voce ja possui uma solicitacao ativa para esta obra.')


@transaction.atomic
def criar_reserva_em_fila(usuario, livro):
    sincronizar_reservas_ativas()
    validar_reserva_ativa(usuario, livro)

    if Exemplar.objects.filter(livro=livro, status=Exemplar.Status.DISPONIVEL).exists():
        raise ValidationError('Esta obra possui exemplar disponivel. Use a guia de emprestimos.')

    return Reserva.objects.create(
        livro=livro,
        usuario=usuario,
        tipo=Reserva.Tipo.FILA,
    )


@transaction.atomic
def criar_solicitacao_emprestimo(usuario, livro):
    sincronizar_reservas_ativas()
    validar_reserva_ativa(usuario, livro)

    exemplar = (
        Exemplar.objects.filter(livro=livro, status=Exemplar.Status.DISPONIVEL)
        .order_by('codigo_tombo')
        .first()
    )
    if exemplar is None:
        raise ValidationError('Nao ha exemplar disponivel para esta obra no momento.')

    exemplar.status = Exemplar.Status.RESERVADO
    exemplar.save(update_fields=['status'])

    return Reserva.objects.create(
        livro=livro,
        usuario=usuario,
        exemplar=exemplar,
        tipo=Reserva.Tipo.RETIRADA,
        data_expiracao=timezone.localdate() + timedelta(days=PRAZO_RESERVA_DIAS),
    )
