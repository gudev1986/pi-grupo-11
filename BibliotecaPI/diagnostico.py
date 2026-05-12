"""
VIEW TEMPORÁRIA DE DIAGNÓSTICO — remova após resolver o problema.

Adicione ao urls.py principal (BibliotecaPI/urls.py):
    from django.urls import path
    from diagnostico import diagnostico_view
    urlpatterns = [..., path('_diagnostico/', diagnostico_view)]
"""
from django.db import connection
from django.http import JsonResponse


def diagnostico_view(request):
    # Migrations registradas no banco
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT app, name FROM django_migrations ORDER BY app, name;"
        )
        migrations_aplicadas = cursor.fetchall()

    # Colunas reais da tabela catalogo_livro
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'catalogo_livro'
            ORDER BY ordinal_position;
        """)
        colunas_livro = [r[0] for r in cursor.fetchall()]

    # Tabelas existentes no banco
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tabelas = [r[0] for r in cursor.fetchall()]

    return JsonResponse({
        'migrations_no_banco': [{'app': a, 'migration': n} for a, n in migrations_aplicadas],
        'colunas_catalogo_livro': colunas_livro,
        'tabelas_existentes': tabelas,
    }, json_dumps_params={'indent': 2})
