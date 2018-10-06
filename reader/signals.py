from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models


@receiver(post_save, sender=models.User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        models.ReaderProfile.objects.create(user=instance)


@receiver(post_save, sender=models.User)
def save_user_profile(sender, instance, **kwargs):
    instance.reader_profile.save()
