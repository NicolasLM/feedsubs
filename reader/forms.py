from django.forms import ModelForm

from . import models


class SubscriptionTagsForm(ModelForm):

    class Meta:
        model = models.Subscription
        fields = ['tags']
