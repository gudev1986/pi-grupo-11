from django import forms

from .models import Autor, Categoria, Editora, Livro


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')


class AutorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Autor
        fields = ['nome']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class EditoraForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Editora
        fields = ['nome']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class CategoriaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class LivroForm(BootstrapFormMixin, forms.ModelForm):
    quantidade_exemplares = forms.IntegerField(
        min_value=1,
        initial=1,
        label='Quantidade de Exemplares',
        help_text='Quantos exemplares deste livro estão sendo adicionados ao acervo?'
    )

    class Meta:
        model = Livro
        fields = [
            'titulo',
            'isbn_10',
            'isbn_13',
            'categoria',
            'ano_publicacao',
            'autores',
            'editora',
        ]
        widgets = {
            'autores': forms.SelectMultiple(attrs={'size': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar os choices
        self.fields['autores'].queryset = Autor.objects.order_by('nome')
        self.fields['editora'].queryset = Editora.objects.order_by('nome')
        self.fields['categoria'].queryset = Categoria.objects.order_by('nome')
        self._apply_bootstrap()


class BuscaAcervoForm(forms.Form):
    q = forms.CharField(required=False, label='Título', widget=forms.TextInput(attrs={'placeholder': 'Buscar por título'}))
    autor = forms.CharField(required=False, label='Autor', widget=forms.TextInput(attrs={'placeholder': 'Nome do autor'}))
    isbn = forms.CharField(required=False, label='ISBN (10 ou 13)')
    categoria = forms.ModelChoiceField(queryset=Categoria.objects.none(), required=False, empty_label='Todas')
    disponivel = forms.BooleanField(required=False, label='Somente disponíveis')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.order_by('nome')
        self._apply_bootstrap()

    def _apply_bootstrap(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')
