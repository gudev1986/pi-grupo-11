from django import forms
from django.utils import timezone

from apps.acervo.models import Exemplar

from .models import Emprestimo, Reserva

PRAZO_EMPRESTIMO_DIAS = 7
PRAZO_RESERVA_DIAS = 3


class EmprestimoForm(forms.ModelForm):
    """
    Formulário de empréstimo simplificado.
    A data de devolução é calculada automaticamente como hoje + 7 dias.
    """
    class Meta:
        model = Emprestimo
        fields = ['exemplar', 'usuario']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['exemplar'].queryset = (
            Exemplar.objects.filter(status=Exemplar.Status.DISPONIVEL)
            .select_related('livro')
        )
        for field in self.fields.values():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.data_prevista_devolucao = (
            timezone.localdate() + __import__('datetime').timedelta(days=PRAZO_EMPRESTIMO_DIAS)
        )
        if commit:
            instance.save()
        return instance


class ReservaForm(forms.ModelForm):
    """
    Formulário de reserva simplificado.
    A data de expiração é calculada automaticamente como hoje + 3 dias.
    """
    class Meta:
        model = Reserva
        fields = ['livro']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')


class DevolucaoForm(forms.Form):
    """
    Confirma a devolução. A data é sempre hoje (preenchida automaticamente na view).
    Mantemos o form apenas para o csrf_token e confirmação do POST.
    """
    pass
