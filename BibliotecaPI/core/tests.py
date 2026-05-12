from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.acervo.models import Exemplar
from apps.catalogo.models import Autor, Categoria, Editora, Livro
from apps.circulacao.models import Emprestimo
from apps.usuarios.constants import ROLE_BIBLIOTECARIO, ROLE_LEITOR
from core.models import PerfilUsuario


class BibliotecaFlowTests(TestCase):

    def create_user(self, username, role=ROLE_LEITOR, precisa_trocar_senha=False):
        user = User.objects.create_user(username=username, password='SenhaForte123!')
        PerfilUsuario.objects.create(
            user=user,
            matricula=f'MAT-{username.upper()}',
            precisa_trocar_senha=precisa_trocar_senha,
        )
        if role:
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
        return user

    def create_book_with_exemplar(self, titulo='Python Profissional', status=Exemplar.Status.DISPONIVEL):
        autor = Autor.objects.create(nome=f'Autor {titulo}')
        editora = Editora.objects.create(nome=f'Editora {titulo}')
        categoria = Categoria.objects.create(nome=f'Categoria {titulo}')
        livro = Livro.objects.create(
            titulo=titulo,
            isbn=f'97812345{Livro.objects.count():05d}',
            ano_publicacao=2025,
            editora=editora,
            categoria=categoria,
        )
        livro.autores.add(autor)
        exemplar = Exemplar.objects.create(
            livro=livro,
            codigo_tombo=f'TOMBO-{Livro.objects.count():05d}',
            status=status,
        )
        return livro, exemplar

    def test_login_e_redirecionamento_home(self):
        self.create_user('leitor01', role=ROLE_LEITOR)

        response_anon = self.client.get(reverse('home'))
        self.assertRedirects(response_anon, '/login/?next=/')

        login_ok = self.client.login(username='leitor01', password='SenhaForte123!')
        self.assertTrue(login_ok)

        response_auth = self.client.get(reverse('home'))
        self.assertEqual(response_auth.status_code, 200)

    def test_troca_obrigatoria_de_senha(self):
        user = self.create_user('troca01', role=ROLE_LEITOR, precisa_trocar_senha=True)
        self.client.force_login(user)

        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('trocar_senha'))

    def test_cadastro_basico_de_livro(self):
        bibliotecario = self.create_user('biblio01', role=ROLE_BIBLIOTECARIO)
        autor = Autor.objects.create(nome='Machado de Assis')
        editora = Editora.objects.create(nome='Editora Central')
        categoria = Categoria.objects.create(nome='Classicos')

        self.client.force_login(bibliotecario)
        response = self.client.post(
            reverse('catalogo:livro_create'),
            data={
                'titulo': 'Dom Casmurro',
                'isbn': '9788535914849',
                'ano_publicacao': 1899,
                'autores': [autor.id],
                'editora': editora.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Livro.objects.filter(titulo='Dom Casmurro').exists())

    def test_busca_de_acervo(self):
        user = self.create_user('leitor02', role=ROLE_LEITOR)
        livro_python, _ = self.create_book_with_exemplar(titulo='Python Profissional', status=Exemplar.Status.DISPONIVEL)
        self.create_book_with_exemplar(titulo='Historia Antiga', status=Exemplar.Status.EMPRESTADO)

        self.client.force_login(user)
        response = self.client.get(
            reverse('catalogo:livro_list'),
            data={'q': 'Python', 'disponivel': 'on'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['livros']), [livro_python])
        self.assertContains(response, livro_python.titulo)

    def test_formulario_catalogo_renderiza_titulo_sem_meta_privado(self):
        bibliotecario = self.create_user('biblio_form', role=ROLE_BIBLIOTECARIO)
        self.client.force_login(bibliotecario)

        response = self.client.get(reverse('catalogo:autor_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<strong>Autor</strong>', html=True)
        self.assertContains(response, 'href="/catalogo/autores/"')

    def test_mensagem_de_permissao_usa_alert_danger(self):
        leitor = self.create_user('leitor_perm', role=ROLE_LEITOR)
        self.client.force_login(leitor)

        response = self.client.get(reverse('acervo:exemplar_list'), follow=True)

        self.assertRedirects(response, reverse('home'))
        self.assertContains(response, 'alert-danger')
        self.assertContains(response, 'Você não possui permissão para acessar esta área.')

    def test_exclusao_de_autor_exibe_mensagem_de_sucesso(self):
        bibliotecario = self.create_user('biblio_delete', role=ROLE_BIBLIOTECARIO)
        autor = Autor.objects.create(nome='Autor Temporario')
        self.client.force_login(bibliotecario)

        response = self.client.post(reverse('catalogo:autor_delete', args=[autor.id]), follow=True)

        self.assertRedirects(response, reverse('catalogo:autor_list'))
        self.assertContains(response, 'alert-success')
        self.assertContains(response, 'Autor excluído com sucesso.')

    def test_paginacao_do_catalogo_preserva_filtros(self):
        user = self.create_user('leitor_page', role=ROLE_LEITOR)
        for index in range(11):
            self.create_book_with_exemplar(titulo=f'Python Guia {index:02d}')

        self.client.force_login(user)
        response = self.client.get(reverse('catalogo:livro_list'), data={'q': 'Python'})

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('?q=Python', content)
        self.assertIn('page=2', content)

    def test_emprestimo_e_devolucao_alteram_status_exemplar(self):
        bibliotecario = self.create_user('biblio02', role=ROLE_BIBLIOTECARIO)
        leitor = self.create_user('leitor03', role=ROLE_LEITOR)
        _, exemplar = self.create_book_with_exemplar(titulo='Banco de Dados', status=Exemplar.Status.DISPONIVEL)

        self.client.force_login(bibliotecario)
        data_prevista = (timezone.localdate() + timedelta(days=7)).strftime('%Y-%m-%d')

        response_emprestimo = self.client.post(
            reverse('circulacao:emprestimo_create'),
            data={
                'exemplar': exemplar.id,
                'usuario': leitor.id,
                'data_prevista_devolucao': data_prevista,
            },
        )

        self.assertEqual(response_emprestimo.status_code, 302)
        exemplar.refresh_from_db()
        self.assertEqual(exemplar.status, Exemplar.Status.EMPRESTADO)

        emprestimo = Emprestimo.objects.get(exemplar=exemplar, status=Emprestimo.Status.ATIVO)

        response_devolucao = self.client.post(
            reverse('circulacao:registrar_devolucao', args=[emprestimo.id]),
            data={'data_devolucao': timezone.localdate().strftime('%Y-%m-%d')},
        )

        self.assertEqual(response_devolucao.status_code, 302)
        exemplar.refresh_from_db()
        emprestimo.refresh_from_db()
        self.assertEqual(exemplar.status, Exemplar.Status.DISPONIVEL)
        self.assertEqual(emprestimo.status, Emprestimo.Status.DEVOLVIDO)

    def test_devolucao_nao_aceita_data_anterior_ao_emprestimo(self):
        bibliotecario = self.create_user('biblio03', role=ROLE_BIBLIOTECARIO)
        leitor = self.create_user('leitor04', role=ROLE_LEITOR)
        _, exemplar = self.create_book_with_exemplar(titulo='Engenharia de Software', status=Exemplar.Status.DISPONIVEL)

        self.client.force_login(bibliotecario)
        self.client.post(
            reverse('circulacao:emprestimo_create'),
            data={
                'exemplar': exemplar.id,
                'usuario': leitor.id,
                'data_prevista_devolucao': (timezone.localdate() + timedelta(days=7)).strftime('%Y-%m-%d'),
            },
        )
        emprestimo = Emprestimo.objects.get(exemplar=exemplar, status=Emprestimo.Status.ATIVO)
        data_invalida = (emprestimo.data_emprestimo - timedelta(days=1)).strftime('%Y-%m-%d')

        response = self.client.post(
            reverse('circulacao:registrar_devolucao', args=[emprestimo.id]),
            data={'data_devolucao': data_invalida},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'data_devolucao', 'A data de devolução não pode ser anterior ao empréstimo.')
        exemplar.refresh_from_db()
        emprestimo.refresh_from_db()
        self.assertEqual(exemplar.status, Exemplar.Status.EMPRESTADO)
        self.assertEqual(emprestimo.status, Emprestimo.Status.ATIVO)
