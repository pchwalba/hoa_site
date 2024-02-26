from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .froms import ArticleForm
from .models import Article
from management.views import AdminStaffRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin


class ArticleListView(ListView):
    template_name = 'article-list.html'
    model = Article
    queryset = Article.objects.all().order_by('-pub_date')
    paginate_by = 5


class ArticleCreate(AdminStaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'article-create.html'
    success_message = "Artykuł stworzony pomyślnie"
    success_url = reverse_lazy('base')


class ArticleUpdate(AdminStaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'article-create.html'
    success_message = "Artykuł edytowany pomyślnie"
    success_url = reverse_lazy('base')


class ArticleDelete(AdminStaffRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Article
    template_name = 'article-confirm-delete.html'
    success_message = "Artykuł usunięty pomyślnie"
    success_url = reverse_lazy('base')


class DownloadsView(TemplateView):
    template_name = 'downloads.html'