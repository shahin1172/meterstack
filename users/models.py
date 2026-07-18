from django.db import models
from django.db.models import TextChoices
from tenants.models import Tenant
from django . contrib . auth . models import AbstractUser


class User(AbstractUser):
    class Role(TextChoices):
        admin='admin','admin'
        member='member','member'
    tenant=models.ForeignKey(Tenant,on_delete=models.CASCADE,related_name='users')
    role=models.CharField(choices=Role.choices,default=Role.member)


    def __str__(self):
        return f'{self.username} {self.tenant}'

# Create your models here.
