from django import forms


class DeleteUserForm(forms.Form):
    username = forms.CharField(
        help_text='Confirm account deletion by entering your username'
    )

    def __init__(self, current_username, *args, **kwargs):
        self._current_username = current_username
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self._current_username != cleaned_data['username']:
            raise forms.ValidationError('Enter your current username')
