from allauth.account.signals import user_logged_in
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models
from .tasks import tasks


@receiver(post_save, sender=models.Feed)
def post_save_feed(sender, instance, created, **kwargs):
    if not created:
        return
    tasks.schedule('synchronize_feed', instance.id)


@receiver(post_save, sender=models.User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        models.Profile.objects.create(user=instance)


@receiver(post_save, sender=models.User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(user_logged_in)
def post_user_logged_in(request, user, **kwargs):
    if not user.profile.deletion_pending:
        return
    user.profile.deletion_pending = False
    user.profile.save()
    messages.add_message(
        request, messages.INFO,
        'Your account was pending deletion, it has now been re-enabled'
    )
