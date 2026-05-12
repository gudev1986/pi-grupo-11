from django import forms


class ImportacaoCSVForm(forms.Form):
    arquivo = forms.FileField(
        label='Arquivo CSV',
        help_text='Selecione um arquivo .csv no formato do template.',
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data['arquivo']
        nome = arquivo.name.lower()
        if not nome.endswith('.csv'):
            raise forms.ValidationError('O arquivo deve ter extensão .csv.')
        return arquivo
