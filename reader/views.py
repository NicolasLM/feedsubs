from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView, ListView, CreateView, DetailView
)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from . import models


class Home(TemplateView):

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['articles'] = (
                models.Article.objects
                .filter(feed__in=self.request.user.reader_profile.feeds.all())
                .prefetch_related('read_by', 'stared_by', 'feed')
            )
        return context

    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ['reader/home_authenticated.html']
        return ['reader/home.html']


class FeedList(LoginRequiredMixin, ListView):
    model = models.Feed
    ordering = 'created_at'

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        rv = (
            super().get_queryset()
            .filter(subscribers=self.request.user.reader_profile)
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
        self.object.subscribers.add(self.request.user.reader_profile)
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class ToggleView(LoginRequiredMixin, View):
    model = None
    attribute_name = None
    add = True

    def post(self, request, pk):
        reader_profile = request.user.reader_profile
        obj = get_object_or_404(self.model, pk=pk)
        profile_set = getattr(obj, self.attribute_name)
        if self.add is True:
            profile_set.add(reader_profile)
        else:
            profile_set.remove(reader_profile)
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
