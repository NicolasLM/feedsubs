from django import forms
from django.forms import ModelForm

from . import models, fields


class SubscriptionTagsForm(ModelForm):

    class Meta:
        model = models.Subscription
        fields = ['tags']


class UploadOPMLFileForm(forms.Form):
    opml_uris = fields.OPMLField(max_length=1024*1024)
