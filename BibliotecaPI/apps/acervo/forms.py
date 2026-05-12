from django import forms

from .models import Exemplar


class ExemplarForm(forms.ModelForm):
    class Meta:
        model = Exemplar
        fields = [
            'livro',
            'codigo_tombo',
            'status',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')
