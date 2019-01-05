from allauth.account.views import EmailView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.views.generic.edit import FormView
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _, gettext_noop as _noop

from . import models, forms, tasks
from .settings import UM_DELETE_ACCOUNT_AFTER


class CurrentPageSettings:
    current_settings = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_settings'] = self.current_settings
        return context


class AccountSettings(CurrentPageSettings, LoginRequiredMixin,
                      SuccessMessageMixin, FormView):
    template_name = 'um/settings_account.html'
    current_settings = _noop('Account')
    form_class = forms.DeleteUserForm
    success_url = reverse_lazy('reader:home')
    success_message = _(
        'The account will be permanently deleted in %d hours, sign in again '
        'to reactivate it'
    ) % int(UM_DELETE_ACCOUNT_AFTER.total_seconds() / 3600)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'current_username': self.request.user.username
        })
        return kwargs

    def form_valid(self, form):
        self.request.user.um_profile.deletion_pending = True
        self.request.user.um_profile.save()
        tasks.tasks.schedule_at(
            'um:delete_user',
            now() + UM_DELETE_ACCOUNT_AFTER,
            self.request.user.id
        )
        logout(self.request)
        return super().form_valid(form)


class InterfaceSettings(CurrentPageSettings, LoginRequiredMixin, UpdateView):
    model = models.UMProfile
    fields = ['language', 'items_per_page']
    template_name = 'um/settings_interface.html'
    success_url = reverse_lazy('um:settings-interface')
    current_settings = _noop('Interface')

    def get_object(self, *args, **kwargs):
        return self.request.user.um_profile


class EmailSettings(CurrentPageSettings, LoginRequiredMixin, EmailView):
    template_name = 'um/settings_email.html'
    success_url = reverse_lazy('um:settings-email')
    current_settings = _noop('Email')


class SecuritySettings(CurrentPageSettings, LoginRequiredMixin,
                       PasswordChangeView):
    template_name = 'um/settings_security.html'
    success_url = reverse_lazy('um:settings-security')
    current_settings = _noop('Security')
