from django.db import models
from users.models import User


class AuditLog(models.Model):
    action = models.CharField(max_length=100)
    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='performed_logs'
    )
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='target_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.performed_by} → {self.action} → {self.target_user}"
