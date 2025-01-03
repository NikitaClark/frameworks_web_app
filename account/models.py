from django.db import models
from django.conf import settings
import os
from django.utils import timezone
from django.core.management.base import BaseCommand

class AccountInvoiceToken(models.Model):
    # Определите поля таблицы account_invoicetoken
    token = models.CharField(max_length=100)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return self.token
class InvoiceToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    invoice_number = models.CharField(max_length=255, unique=True)
    tokens_credited = models.IntegerField(default=0)

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='user/%Y/%m%d', blank=True)
    tokens = models.IntegerField(default=0)
    group_expiration_date = models.DateTimeField(null=True, blank=True)
    invoice_number = models.CharField(max_length=20, default='DEFAULT_INVOICE')  # Добавляем поле для инвойса с значением по умолчанию

    def __str__(self):
        return f'Profile of {self.user.username}'

class VideoLink(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    link = models.URLField()
    filename = models.CharField(max_length=255, default='default_filename.mp4')  # Set a default value
    file_path = models.FilePathField(path= 'media')
    thumbnail_path = models.FilePathField(path= 'media',default='', blank=True)  # Ensure thumbnail path is also handled
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"VideoLink(id={self.id}, user={self.user.username}, link={self.link}, filename={self.filename})"
    
    @property 
    def file_name(self):
        return os.path.basename(self.link) if self.link else 'No name'
    from django.db import models

class Invoice(models.Model):
    invoice_id = models.CharField(max_length=100, unique=True)
    customer_name = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Invoice {self.invoice_id} for {self.customer_name}'
