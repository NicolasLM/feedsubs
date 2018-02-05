from django.contrib.auth.models import User
from django.db import models


class UMProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='um_profile')
    night_mode = models.BooleanField(default=False)
    deletion_pending = models.BooleanField(default=False)

    def __str__(self):
        return 'UMProfile of {}'.format(self.user)
