from django import forms
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from allauth.account.forms import SignupForm


class DeleteUserForm(forms.Form):
    username = forms.CharField(
        label=_('Username'),
        help_text=_('Confirm account deletion by entering your username')
    )

    def __init__(self, current_username, *args, **kwargs):
        self._current_username = current_username
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self._current_username != cleaned_data['username']:
            raise forms.ValidationError(_('Enter your current username'))


class SignupFormWithToS(SignupForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tos_page = reverse_lazy('django.contrib.flatpages.views.flatpage',
                                kwargs={'url': '/terms-of-service'})
        label = mark_safe(_('I have read and I agree with the <a href="%s">'
                            'Terms of Service</a>') % tos_page)
        self.fields['tos'] = forms.BooleanField(required=True, label=label)
