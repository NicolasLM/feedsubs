from allauth.account.signals import user_logged_in
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models


@receiver(post_save, sender=models.User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        models.UMProfile.objects.create(user=instance)


@receiver(post_save, sender=models.User)
def save_user_profile(sender, instance, **kwargs):
    instance.um_profile.save()


@receiver(user_logged_in)
def post_user_logged_in(request, user, **kwargs):
    if not user.um_profile.deletion_pending:
        return
    user.um_profile.deletion_pending = False
    user.um_profile.save()
    messages.add_message(
        request, messages.INFO,
        'Your account was pending deletion, it has now been re-enabled'
    )
