from datetime import timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.acervo.models import Exemplar

from .models import Emprestimo, Reserva
from .services import PRAZO_EMPRESTIMO_DIAS, PRAZO_RESERVA_DIAS

User = get_user_model()


class EmprestimoForm(forms.ModelForm):
    class Meta:
        model = Emprestimo
        fields = ['exemplar', 'usuario']

    def __init__(self, *args, reserva=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.reserva = reserva

        exemplares = Exemplar.objects.select_related('livro')
        if reserva and reserva.exemplar_id:
            exemplares = exemplares.filter(pk=reserva.exemplar_id)
        elif reserva:
            exemplares = exemplares.filter(livro=reserva.livro, status=Exemplar.Status.DISPONIVEL)
        else:
            exemplares = exemplares.filter(status=Exemplar.Status.DISPONIVEL)
        self.fields['exemplar'].queryset = exemplares

        if reserva:
            self.fields['usuario'].queryset = User.objects.filter(pk=reserva.usuario_id)
        else:
            self.fields['usuario'].queryset = User.objects.all()

        for field in self.fields.values():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.data_prevista_devolucao = timezone.localdate() + timedelta(days=PRAZO_EMPRESTIMO_DIAS)
        if commit:
            instance.save()
        return instance


class ReservaBuscaForm(forms.Form):
    q = forms.CharField(required=False, label='Palavra-chave no Titulo', widget=forms.TextInput(attrs={'placeholder': 'Ex: Dom Casmurro'}))
    autor = forms.CharField(required=False, label='Autor', widget=forms.TextInput(attrs={'placeholder': 'Ex: Machado de Assis'}))
    isbn = forms.CharField(required=False, label='ISBN (10 ou 13)', widget=forms.TextInput(attrs={'placeholder': 'Ex: 9788544001820'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['livro']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['livro'].widget.attrs.update({'data-placeholder': 'Busque e selecione o livro'})
        for field in self.fields.values():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')


class DevolucaoForm(forms.Form):
    pass
