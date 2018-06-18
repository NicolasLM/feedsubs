from django import forms
from django.forms import ModelForm

from . import models


class SubscriptionTagsForm(ModelForm):

    class Meta:
        model = models.Subscription
        fields = ['tags']


class UploadOPMLFileForm(forms.Form):
    file = forms.FileField(max_length=1024*1024)
