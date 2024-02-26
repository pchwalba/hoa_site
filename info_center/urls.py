from django.urls import path
from .views import *

urlpatterns = [
    path('', ArticleListView.as_view(), name='base'),
    path('article/create', ArticleCreate.as_view(), name='article-create'),
    path('article/edit/<int:pk>', ArticleUpdate.as_view(), name='article-update'),
    path('article/delete/<int:pk>', ArticleDelete.as_view(), name='article-delete'),
    path('downloads/', DownloadsView.as_view(), name='downloads'),
]
