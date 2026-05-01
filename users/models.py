from django.db import models
from django.contrib.auth.models import AbstractUser
from tenants.models import Tenant

#user model
class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE,related_name='users',null=True, blank=True)

    def __str__(self):
        return self.username