from django.db import models

class TaskFile(models.Model):
    id = models.AutoField(primary_key=True)

    task_name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_path = models.CharField(max_length=500, null=True, blank=True)

    status = models.CharField(max_length=20, default='pending')

    result_json = models.JSONField(null=True, blank=True)
    error_msg = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'task_file'
        managed = True

    def __str__(self):
        return f"{self.task_name} ({self.status})"
