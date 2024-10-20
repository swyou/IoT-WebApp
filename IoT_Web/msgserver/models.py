from django.db import models

# Create your models here.


class Message(models.Model):
    payload = models.TextField()
    timestamp = models.DateTimeField()

    class Meta:
        ordering = ['-timestamp']