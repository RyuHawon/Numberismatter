from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Character


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_character(sender, instance, created, **kwargs):
    if created:
        Character.objects.create(user=instance)
