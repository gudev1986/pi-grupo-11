from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.acervo.models import Exemplar
from apps.catalogo.models import Autor, Categoria, Editora, Livro

from .models import Emprestimo, Reserva
from .services import criar_solicitacao_emprestimo

User = get_user_model()


class CirculacaoFluxoTests(TestCase):
    def setUp(self):
        self.leitor = User.objects.create_user(username='leitor', password='SenhaForte123!')
        self.outro_leitor = User.objects.create_user(username='outro', password='SenhaForte123!')
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='SenhaForte123!',
        )

    def criar_livro(self, titulo, status=Exemplar.Status.DISPONIVEL):
        autor = Autor.objects.create(nome=f'Autor {titulo}')
        editora = Editora.objects.create(nome=f'Editora {titulo}')
        categoria = Categoria.objects.create(nome=f'Categoria {titulo}')
        livro = Livro.objects.create(
            titulo=titulo,
            isbn_10=f'{Livro.objects.count() + 1:010d}',
            isbn_13=f'{Livro.objects.count() + 1:013d}',
            ano_publicacao=2026,
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

    def criar_emprestimo_ativo(self, livro, exemplar, usuario, dias=5):
        exemplar.status = Exemplar.Status.EMPRESTADO
        exemplar.save(update_fields=['status'])
        return Emprestimo.objects.create(
            exemplar=exemplar,
            usuario=usuario,
            data_prevista_devolucao=timezone.localdate() + timedelta(days=dias),
        )

    def test_usuario_visualiza_obras_indisponiveis_na_guia_reservas(self):
        livro_indisponivel, exemplar_indisponivel = self.criar_livro('Livro Reservavel', status=Exemplar.Status.EMPRESTADO)
        self.criar_emprestimo_ativo(livro_indisponivel, exemplar_indisponivel, self.outro_leitor, dias=4)
        self.criar_livro('Livro Disponivel', status=Exemplar.Status.DISPONIVEL)

        self.client.force_login(self.leitor)
        response = self.client.get(reverse('circulacao:reserva_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nova reserva')
        self.assertContains(response, 'Pesquisar e criar reserva')
        self.assertContains(response, 'Livro Reservavel')
        self.assertContains(response, (timezone.localdate() + timedelta(days=4)).strftime('%d/%m/%Y'))
        self.assertNotContains(response, 'Livro Disponivel')

    def test_usuario_entra_na_fila_de_reserva_quando_nao_ha_disponibilidade(self):
        livro, exemplar = self.criar_livro('Fila de Espera', status=Exemplar.Status.EMPRESTADO)
        self.criar_emprestimo_ativo(livro, exemplar, self.outro_leitor, dias=6)

        self.client.force_login(self.leitor)
        response = self.client.post(reverse('circulacao:solicitar_reserva', args=[livro.id]))

        self.assertEqual(response.status_code, 302)
        reserva = Reserva.objects.get(usuario=self.leitor, livro=livro)
        self.assertEqual(reserva.tipo, Reserva.Tipo.FILA)
        self.assertEqual(reserva.status, Reserva.Status.ATIVA)
        self.assertIsNone(reserva.exemplar)
        self.assertTrue(reserva.protocolo)

    def test_usuario_solicita_emprestimo_e_recebe_protocolo_de_retirada(self):
        livro, exemplar = self.criar_livro('Retirada Imediata', status=Exemplar.Status.DISPONIVEL)

        self.client.force_login(self.leitor)
        response = self.client.post(reverse('circulacao:solicitar_emprestimo', args=[livro.id]))

        self.assertEqual(response.status_code, 302)
        reserva = Reserva.objects.get(usuario=self.leitor, livro=livro)
        exemplar.refresh_from_db()
        self.assertEqual(reserva.tipo, Reserva.Tipo.RETIRADA)
        self.assertEqual(reserva.status, Reserva.Status.ATIVA)
        self.assertEqual(reserva.exemplar_id, exemplar.id)
        self.assertTrue(reserva.protocolo)
        self.assertEqual(exemplar.status, Exemplar.Status.RESERVADO)

    def test_guia_emprestimos_do_usuario_limita_resultados_e_permite_busca(self):
        for indice in range(6):
            self.criar_livro(f'Livro Disponivel {indice}', status=Exemplar.Status.DISPONIVEL)

        self.client.force_login(self.leitor)

        response = self.client.get(reverse('circulacao:emprestimo_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buscar obras disponiveis')
        for indice in range(5):
            self.assertContains(response, f'Livro Disponivel {indice}')
        self.assertNotContains(response, 'Livro Disponivel 5')

        busca_response = self.client.get(reverse('circulacao:emprestimo_list'), data={'q': '5'})

        self.assertEqual(busca_response.status_code, 200)
        self.assertContains(busca_response, 'Livro Disponivel 5')
        self.assertNotContains(busca_response, 'Livro Disponivel 0')

    def test_admin_converte_reserva_pronta_em_emprestimo(self):
        livro, exemplar = self.criar_livro('Livro Pronto', status=Exemplar.Status.DISPONIVEL)
        reserva = criar_solicitacao_emprestimo(self.leitor, livro)

        self.client.force_login(self.admin)
        list_response = self.client.get(reverse('circulacao:reserva_list'))
        self.assertContains(list_response, 'Abrir emprestimo')
        self.assertContains(list_response, reserva.protocolo)

        create_url = f"{reverse('circulacao:emprestimo_create')}?reserva={reserva.id}&next={reverse('circulacao:reserva_list')}"
        response = self.client.post(create_url, data={
            'usuario': self.leitor.id,
            'exemplar': exemplar.id,
        })

        self.assertRedirects(response, reverse('circulacao:reserva_list'))
        reserva.refresh_from_db()
        exemplar.refresh_from_db()
        self.assertEqual(reserva.status, Reserva.Status.ATENDIDA)
        self.assertEqual(exemplar.status, Exemplar.Status.EMPRESTADO)
        self.assertTrue(Emprestimo.objects.filter(exemplar=exemplar, usuario=self.leitor).exists())
