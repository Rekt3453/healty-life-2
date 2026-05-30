from django.db import models


class AuditLog(models.Model):
    id_log = models.BigAutoField(primary_key=True)
    id_user = models.BigIntegerField(blank=True, null=True)
    role = models.CharField(max_length=50)
    action = models.CharField(max_length=50)
    model_affected = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.BigIntegerField(blank=True, null=True)
    details = models.JSONField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'audit_log'
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.role} | {self.action} | {self.model_affected or '—'}"
