from allauth.account.signals import user_logged_in
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _, get_language

from . import models, utils


@receiver(post_save, sender=models.User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        models.UMProfile.objects.create(user=instance, language=get_language())


@receiver(post_save, sender=models.User)
def save_user_profile(sender, instance, **kwargs):
    instance.um_profile.save()


@receiver(user_logged_in)
def post_user_logged_in(request, user, **kwargs):
    utils.set_session_language_if_necessary(request, user)

    if user.um_profile.deletion_pending:
        user.um_profile.deletion_pending = False
        user.um_profile.save()
        messages.add_message(
            request, messages.INFO,
            _('Your account was pending deletion, it has now been re-enabled')
        )
