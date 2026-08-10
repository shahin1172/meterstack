import random
import secrets
from django . db import models
from django.db import models

class Tenant(models.Model):
    name=models.CharField(max_length=300)
    slug=models.SlugField(max_length=100,db_index=True,unique=True)
    api_key=models.CharField(max_length=64,unique=True,db_index=True,editable=False)
    created_at=models.DateTimeField(auto_now_add=True)
    is_active=models.BooleanField(default=True)

    def save(self,*args,**kwargs):
        if not self.api_key:
            self.api_key=secrets.token_urlsafe(48)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name

# Create your models here.
