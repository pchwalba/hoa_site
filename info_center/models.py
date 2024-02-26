from django.db import models


# Create your models here.

class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name='Tytuł')
    content = models.TextField(verbose_name='Treść')
    pub_date = models.DateTimeField(auto_now=True, verbose_name='Data publikacji')

    def __str__(self):
        return f"{self.title} - {self.pub_date}"
