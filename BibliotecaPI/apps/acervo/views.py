from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.usuarios.permissions import AdminOrBibliotecarioRequiredMixin

from .forms import ExemplarForm
from .models import Exemplar


class ExemplarListView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, ListView):
    model = Exemplar
    template_name = 'acervo/exemplar_list.html'
    context_object_name = 'exemplares'
    paginate_by = 20

    def get_queryset(self):
        queryset = Exemplar.objects.select_related('livro')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(livro__titulo__icontains=q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


class ExemplarCreateView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, SuccessMessageMixin, CreateView):
    model = Exemplar
    form_class = ExemplarForm
    template_name = 'acervo/form.html'
    success_url = reverse_lazy('acervo:exemplar_list')
    success_message = 'Exemplar cadastrado com sucesso.'


class ExemplarUpdateView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Exemplar
    form_class = ExemplarForm
    template_name = 'acervo/form.html'
    success_url = reverse_lazy('acervo:exemplar_list')
    success_message = 'Exemplar atualizado com sucesso.'


class ExemplarDeleteView(LoginRequiredMixin, AdminOrBibliotecarioRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Exemplar
    template_name = 'acervo/confirm_delete.html'
    success_url = reverse_lazy('acervo:exemplar_list')
    success_message = 'Exemplar excluído com sucesso.'
