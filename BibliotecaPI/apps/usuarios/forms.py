from django import forms
from django.contrib.auth.models import Group, User

from core.models import PerfilUsuario

from .constants import ROLE_CHOICES
from .utils import ensure_default_groups


class UsuarioCadastroForm(forms.ModelForm):
    matricula = forms.CharField(max_length=20, required=True, label='Matrícula')
    senha = forms.CharField(widget=forms.PasswordInput, required=True, label='Senha inicial')
    papel = forms.ChoiceField(choices=ROLE_CHOICES, required=True, label='Papel')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'papel':
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean_matricula(self):
        matricula = self.cleaned_data['matricula'].strip()
        if PerfilUsuario.objects.filter(matricula__iexact=matricula).exists():
            raise forms.ValidationError('Já existe um usuário com esta matrícula.')
        return matricula

    def save(self, commit=True):
        ensure_default_groups()
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['senha'])
        if commit:
            user.save()
            group = Group.objects.get(name=self.cleaned_data['papel'])
            user.groups.set([group])
        return user
