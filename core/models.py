from django.db import models
from users.models import User
# Create your models here.
class AuditLog(models.Model):
    action = models.CharField(max_length=50)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='target')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.performed_by} → {self.action} → {self.target_user}"