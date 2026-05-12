import csv
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.acervo.models import Exemplar
from apps.catalogo.models import Autor, Categoria, Editora, Livro
from apps.usuarios.constants import ROLE_ADMIN
from apps.usuarios.utils import user_has_any_role

from .forms import ImportacaoCSVForm


@login_required
def importar_csv(request):
    if not user_has_any_role(request.user, [ROLE_ADMIN]):
        messages.error(request, 'Você não possui permissão para importar dados.')
        return redirect('home')

    erros = []

    if request.method == 'POST':
        form = ImportacaoCSVForm(request.POST, request.FILES)

        if form.is_valid():
            arquivo = request.FILES['arquivo']

            try:
                conteudo = arquivo.read().decode('utf-8-sig')  # utf-8-sig suporta BOM do Excel
            except UnicodeDecodeError:
                arquivo.seek(0)
                conteudo = arquivo.read().decode('latin-1')

            reader = csv.DictReader(io.StringIO(conteudo))

            livros_importados = 0
            exemplares_criados = 0

            for numero_linha, linha in enumerate(reader, start=2):
                try:
                    titulo = linha.get('titulo', '').strip()
                    isbn = linha.get('isbn', '').strip()
                    nome_autor = linha.get('autor', '').strip()
                    nome_categoria = linha.get('categoria', '').strip()
                    nome_editora = linha.get('editora', '').strip()
                    ano_str = linha.get('ano_publicacao', '').strip()
                    qtd_str = linha.get('quantidade', '1').strip()

                    if not titulo:
                        erros.append(f'Linha {numero_linha}: campo "titulo" obrigatório.')
                        continue

                    # Cria ou recupera autor, categoria, editora
                    autor = None
                    if nome_autor:
                        autor, _ = Autor.objects.get_or_create(nome=nome_autor)

                    categoria = None
                    if nome_categoria:
                        categoria, _ = Categoria.objects.get_or_create(nome=nome_categoria)

                    editora = None
                    if nome_editora:
                        editora, _ = Editora.objects.get_or_create(nome=nome_editora)

                    ano_publicacao = None
                    if ano_str:
                        try:
                            ano_publicacao = int(ano_str)
                        except ValueError:
                            erros.append(f'Linha {numero_linha}: ano_publicacao inválido ("{ano_str}"). Ignorado.')

                    # Cria ou recupera o livro
                    if isbn:
                        livro, criado = Livro.objects.get_or_create(
                            isbn=isbn,
                            defaults={
                                'titulo': titulo,
                                'editora': editora,
                                'categoria': categoria,
                                'ano_publicacao': ano_publicacao,
                            }
                        )
                    else:
                        # Sem ISBN: cria sempre (ou busca por título exato)
                        livro, criado = Livro.objects.get_or_create(
                            titulo=titulo,
                            defaults={
                                'editora': editora,
                                'categoria': categoria,
                                'ano_publicacao': ano_publicacao,
                            }
                        )

                    if criado:
                        livros_importados += 1

                    if autor:
                        livro.autores.add(autor)

                    # Cria exemplares com tombos únicos baseados em timestamp
                    try:
                        quantidade = max(1, int(qtd_str))
                    except ValueError:
                        quantidade = 1

                    ts = timezone.now().strftime('%Y%m%d%H%M%S%f')
                    for i in range(quantidade):
                        # Tombo: ID do livro + timestamp + índice, garante unicidade
                        codigo_tombo = f"{livro.id}-{ts}-{i}"
                        Exemplar.objects.get_or_create(
                            codigo_tombo=codigo_tombo,
                            defaults={'livro': livro},
                        )
                        exemplares_criados += 1

                except Exception as e:
                    erros.append(f'Linha {numero_linha}: erro inesperado — {e}')

            if erros:
                for erro in erros:
                    messages.warning(request, erro)

            messages.success(
                request,
                f'Importação concluída: {livros_importados} livro(s) novo(s), '
                f'{exemplares_criados} exemplar(es) criado(s).'
            )
            return redirect('importacao:importar_csv')

    else:
        form = ImportacaoCSVForm()

    return render(request, 'importacao/importar_csv.html', {'form': form})


@login_required
def download_template_csv(request):
    """Retorna um arquivo CSV de exemplo para o usuário preencher e importar."""
    if not user_has_any_role(request.user, [ROLE_ADMIN]):
        messages.error(request, 'Você não possui permissão para esta ação.')
        return redirect('home')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="template_importacao.csv"'
    response.write('\ufeff')  # BOM para Excel abrir corretamente

    writer = csv.writer(response)
    writer.writerow(['titulo', 'isbn', 'autor', 'editora', 'categoria', 'ano_publicacao', 'quantidade'])
    writer.writerow(['Dom Casmurro', '9788544001820', 'Machado de Assis', 'Penguin-Companhia', 'Romance', '1899', '2'])
    writer.writerow(['O Cortiço', '9788572326995', 'Aluísio Azevedo', 'Ática', 'Romance', '1890', '1'])
    writer.writerow(['Memórias Póstumas de Brás Cubas', '', 'Machado de Assis', 'Nova Fronteira', 'Romance', '1881', '3'])

    return response
