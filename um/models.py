from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class UMProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='um_profile')
    items_per_page = models.PositiveSmallIntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(200)]
    )
    deletion_pending = models.BooleanField(default=False)

    def __str__(self):
        return 'UMProfile of {}'.format(self.user)
