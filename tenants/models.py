from django.db import models

# Create your models here.
class Tenant(models.Model):
    organization_name=models.CharField(max_length=50) #django deafult null and blank nhi hoga
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.organization_name


 