from datetime import timedelta

from allauth.account.views import EmailView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView, ListView, CreateView, DetailView, UpdateView
)
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from . import models, forms, tasks


class Home(TemplateView):
    template_name = 'reader/home.html'

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['articles'] = (
                models.Article.objects
                .filter(feed__in=self.request.user.profile.feeds.all())
                .prefetch_related('read_by', 'stared_by', 'feed')
            )
        else:
            context['articles'] = models.Article.objects.all()[:20]
        return context


class CurrentPageSettings:
    current_settings = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_settings'] = self.current_settings
        return context


class AccountSettings(CurrentPageSettings, LoginRequiredMixin,
                      SuccessMessageMixin, FormView):
    template_name = 'reader/settings_account.html'
    current_settings = 'account'
    form_class = forms.DeleteUserForm
    success_url = reverse_lazy('reader:home')
    success_message = (
        'The account will be permanently deleted in 24 hours, sign in again '
        'to reactivate it.'
    )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'current_username': self.request.user.username
        })
        return kwargs

    def form_valid(self, form):
        self.request.user.profile.deletion_pending = True
        self.request.user.profile.save()
        tasks.tasks.schedule_at('delete_user', self.request.user.id,
                                now() + timedelta(hours=24))
        logout(self.request)
        return super().form_valid(form)


class InterfaceSettings(CurrentPageSettings, LoginRequiredMixin, UpdateView):
    model = models.Profile
    fields = ['night_mode']
    template_name = 'reader/settings_interface.html'
    success_url = reverse_lazy('reader:settings-interface')
    current_settings = 'interface'

    def get_object(self, *args, **kwargs):
        return self.request.user.profile


class EmailSettings(CurrentPageSettings, LoginRequiredMixin, EmailView):
    template_name = 'reader/settings_email.html'
    success_url = reverse_lazy('reader:settings-email')
    current_settings = 'email'


class SecuritySettings(CurrentPageSettings, LoginRequiredMixin,
                       PasswordChangeView):
    template_name = 'reader/settings_security.html'
    success_url = reverse_lazy('reader:settings-security')
    current_settings = 'security'


class FeedList(LoginRequiredMixin, ListView):
    model = models.Feed
    ordering = 'created_at'

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        rv = (
            super().get_queryset()
            .filter(subscribers=self.request.user.profile)
        )
        return rv


class FeedDetail(LoginRequiredMixin, DetailView):
    model = models.Feed

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['articles'] = (
            context['feed'].article_set.all()
            .prefetch_related('read_by', 'stared_by', 'feed')
        )
        return context


class FeedCreate(LoginRequiredMixin, CreateView):
    model = models.Feed
    fields = ['name', 'uri']
    success_url = reverse_lazy('reader:feed-list')

    def form_valid(self, form):
        self.object = form.save()
        self.object.subscribers.add(self.request.user.profile)
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class ToggleView(LoginRequiredMixin, View):
    model = None
    attribute_name = None
    add = True

    def post(self, request, pk):
        profile = request.user.profile
        obj = get_object_or_404(self.model, pk=pk)
        profile_set = getattr(obj, self.attribute_name)
        if self.add is True:
            profile_set.add(profile)
        else:
            profile_set.remove(profile)
        return HttpResponse(status=204)


class StarArticleView(ToggleView):
    model = models.Article
    attribute_name = 'stared_by'
    add = True


class UnstarArticleView(ToggleView):
    model = models.Article
    attribute_name = 'stared_by'
    add = False


class ReadArticleView(ToggleView):
    model = models.Article
    attribute_name = 'read_by'
    add = True


class UnreadArticleView(ToggleView):
    model = models.Article
    attribute_name = 'read_by'
    add = False


class UnsubscribeView(ToggleView):
    model = models.Feed
    attribute_name = 'subscribers'
    add = False
