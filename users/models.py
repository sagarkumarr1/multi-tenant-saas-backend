from django.db import models
from django.contrib.auth.models import AbstractUser
from tenants.models import Tenant

#user model
class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE,related_name='users',null=True, blank=True)
    ADMIN = 'ADMIN'
    MANAGER = 'MANAGER'
    USER_ROLE = 'USER'

        
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (USER_ROLE, 'User'),
    ]
    role = models.CharField(
        max_length=7,
        choices=ROLE_CHOICES,
        default=USER_ROLE,  # Default value set kar di
    )

    created_by = models.ForeignKey(
    'self',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='created_users',
    db_index=True

)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

