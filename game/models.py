from django.conf import settings
from django.db import models


class Character(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='character',
    )