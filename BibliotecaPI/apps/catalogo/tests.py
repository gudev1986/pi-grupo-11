import tempfile
from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.acervo.models import Exemplar

from .forms import LivroForm
from .models import Autor, CapaLivro, Categoria, Editora, Livro


GIF_1X1 = (
    b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00'
    b'\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


class LivroComCapaTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)
        self.media_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

        self.autor = Autor.objects.create(nome='Autora Teste')
        self.editora = Editora.objects.create(nome='Editora Teste')
        self.categoria = Categoria.objects.create(nome='Categoria Teste')

    def test_form_salva_capa_em_tabela_vinculada_ao_livro(self):
        form = LivroForm(
            data={
                'titulo': 'Livro com capa',
                'isbn_10': '1234567890',
                'isbn_13': '1234567890123',
                'categoria': self.categoria.pk,
                'ano_publicacao': 2026,
                'autores': [self.autor.pk],
                'editora': self.editora.pk,
                'quantidade_exemplares': 1,
            },
            files={
                'capa_imagem': SimpleUploadedFile(
                    'capa.gif',
                    GIF_1X1,
                    content_type='image/gif',
                )
            },
        )

        self.assertTrue(form.is_valid(), form.errors)

        livro = form.save()
        form.save_capa(livro)

        capa = CapaLivro.objects.get(livro=livro)
        self.assertTrue(capa.imagem.name.startswith(f'capas/livro_{livro.pk}/'))
        self.assertEqual(livro.capa_imagem.name, capa.imagem.name)

    def test_detalhe_do_livro_exibe_capa_e_exemplares(self):
        user = get_user_model().objects.create_user(username='leitor', password='senha-segura')
        livro = Livro.objects.create(
            titulo='Livro detalhado',
            isbn_10='0987654321',
            isbn_13='3210987654321',
            categoria=self.categoria,
            ano_publicacao=2025,
            editora=self.editora,
        )
        livro.autores.add(self.autor)
        CapaLivro.objects.create(
            livro=livro,
            imagem=SimpleUploadedFile('detalhe.gif', GIF_1X1, content_type='image/gif'),
        )
        Exemplar.objects.create(livro=livro, codigo_tombo='TOMBO-1')

        self.client.force_login(user)
        response = self.client.get(reverse('catalogo:livro_detail', args=[livro.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Capa de Livro detalhado')
        self.assertContains(response, livro.capa_imagem.url)
        self.assertContains(response, 'TOMBO-1')

    def test_formulario_de_adicao_de_exemplares_cria_varios_registros(self):
        admin = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='senha-segura',
        )
        livro = Livro.objects.create(
            titulo='Livro em lote',
            isbn_10='1111111111',
            isbn_13='1111111111111',
            categoria=self.categoria,
            ano_publicacao=2024,
            editora=self.editora,
        )
        livro.autores.add(self.autor)

        self.client.force_login(admin)
        next_url = '/catalogo/?page=2'
        url = f"{reverse('catalogo:livro_adicionar_exemplar', args=[livro.pk])}?next={quote(next_url, safe='')}"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quantidade de exemplares')

        post_response = self.client.post(url, data={'quantidade': 3})

        self.assertRedirects(post_response, next_url, fetch_redirect_response=False)
        self.assertEqual(Exemplar.objects.filter(livro=livro).count(), 3)
