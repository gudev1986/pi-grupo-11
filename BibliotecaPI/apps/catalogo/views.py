from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.acervo.models import Exemplar
from apps.usuarios.permissions import AdminOrBibliotecarioRequiredMixin

from .forms import AutorForm, BuscaAcervoForm, CategoriaForm, EditoraForm, LivroForm
from .models import Autor, Categoria, Editora, Livro


class FormTitleMixin:
    form_title = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = self.form_title or self.model._meta.verbose_name.title()
        return context


class AutorListView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, ListView):
    model = Autor
    template_name = 'catalogo/autor_list.html'
    context_object_name = 'autores'


class AutorCreateView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, FormTitleMixin, SuccessMessageMixin, CreateView):
    model = Autor
    form_class = AutorForm
    template_name = 'catalogo/form.html'
    success_url = reverse_lazy('catalogo:autor_list')
    form_title = 'Autor'
    success_message = 'Autor cadastrado com sucesso.'


class AutorUpdateView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, FormTitleMixin, SuccessMessageMixin, UpdateView):
    model = Autor
    form_class = AutorForm
    template_name = 'catalogo/form.html'
    success_url = reverse_lazy('catalogo:autor_list')
    form_title = 'Autor'
    success_message = 'Autor atualizado com sucesso.'


class AutorDeleteView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Autor
    template_name = 'catalogo/confirm_delete.html'
    success_url = reverse_lazy('catalogo:autor_list')
    success_message = 'Autor excluído com sucesso.'


class EditoraListView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, ListView):
    model = Editora
    template_name = 'catalogo/editora_list.html'
    context_object_name = 'editoras'


class EditoraCreateView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, FormTitleMixin, SuccessMessageMixin, CreateView):
    model = Editora
    form_class = EditoraForm
    template_name = 'catalogo/form.html'
    success_url = reverse_lazy('catalogo:editora_list')
    form_title = 'Editora'
    success_message = 'Editora cadastrada com sucesso.'


class EditoraUpdateView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, FormTitleMixin, SuccessMessageMixin, UpdateView):
    model = Editora
    form_class = EditoraForm
    template_name = 'catalogo/form.html'
    success_url = reverse_lazy('catalogo:editora_list')
    form_title = 'Editora'
    success_message = 'Editora atualizada com sucesso.'


class EditoraDeleteView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Editora
    template_name = 'catalogo/confirm_delete.html'
    success_url = reverse_lazy('catalogo:editora_list')
    success_message = 'Editora excluída com sucesso.'


class CategoriaListView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, ListView):
    model = Categoria
    template_name = 'catalogo/categoria_list.html'
    context_object_name = 'categorias'


class CategoriaCreateView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, FormTitleMixin, SuccessMessageMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'catalogo/form.html'
    success_url = reverse_lazy('catalogo:categoria_list')
    form_title = 'Categoria'
    success_message = 'Categoria cadastrada com sucesso.'


class CategoriaUpdateView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, FormTitleMixin, SuccessMessageMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'catalogo/form.html'
    success_url = reverse_lazy('catalogo:categoria_list')
    form_title = 'Categoria'
    success_message = 'Categoria atualizada com sucesso.'


class CategoriaDeleteView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Categoria
    template_name = 'catalogo/confirm_delete.html'
    success_url = reverse_lazy('catalogo:categoria_list')
    success_message = 'Categoria excluída com sucesso.'


class LivroListView(LoginRequiredMixin, ListView):
    model = Livro
    template_name = 'catalogo/livro_list.html'
    context_object_name = 'livros'
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Livro.objects.select_related('editora', 'categoria')
            .prefetch_related('autores')
            .annotate(total_exemplares=Count('exemplares', distinct=True))
            .annotate(
                exemplares_disponiveis=Count(
                    'exemplares',
                    filter=Q(exemplares__status=Exemplar.Status.DISPONIVEL),
                    distinct=True,
                )
            )
        )

        form = BuscaAcervoForm(self.request.GET or None)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            autor = form.cleaned_data.get('autor')
            isbn = form.cleaned_data.get('isbn')
            categoria = form.cleaned_data.get('categoria')
            disponivel = form.cleaned_data.get('disponivel')

            if q:
                queryset = queryset.filter(titulo__icontains=q)
            if autor:
                queryset = queryset.filter(autores__nome__icontains=autor)
            if isbn:
                queryset = queryset.filter(isbn__icontains=isbn)
            if categoria:
                queryset = queryset.filter(categoria=categoria)
            if disponivel:
                queryset = queryset.filter(exemplares__status=Exemplar.Status.DISPONIVEL)

        return queryset.distinct().order_by('titulo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['busca_form'] = BuscaAcervoForm(self.request.GET or None)
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['query_params'] = query_params.urlencode()
        return context


class LivroDetailView(LoginRequiredMixin, DetailView):
    model = Livro
    template_name = 'catalogo/livro_detail.html'
    context_object_name = 'livro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exemplares'] = self.object.exemplares.order_by('codigo_tombo')
        return context


class LivroCreateView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, FormTitleMixin, SuccessMessageMixin, CreateView):
    model = Livro
    form_class = LivroForm
    template_name = 'catalogo/form.html'
    success_url = reverse_lazy('catalogo:livro_list')
    form_title = 'Livro'
    success_message = 'Livro cadastrado com sucesso.'


class LivroUpdateView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, FormTitleMixin, SuccessMessageMixin, UpdateView):
    model = Livro
    form_class = LivroForm
    template_name = 'catalogo/form.html'
    success_url = reverse_lazy('catalogo:livro_list')
    form_title = 'Livro'
    success_message = 'Livro atualizado com sucesso.'


class LivroDeleteView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Livro
    template_name = 'catalogo/confirm_delete.html'
    success_url = reverse_lazy('catalogo:livro_list')
    success_message = 'Livro excluído com sucesso.'