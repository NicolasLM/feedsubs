from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from . import models


class Home(LoginRequiredMixin, ListView):
    model = models.Article
    template_name = 'reader/home_authenticated.html'
    context_object_name = 'articles'

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(feed__in=self.request.user.reader_profile.feeds.all())
            .exclude(id__in=self.request.user.reader_profile.read.all())
            .prefetch_related('read_by', 'stared_by', 'feed')
        )

    def handle_no_permission(self):
        return render(self.request, 'reader/home.html')

    def get_paginate_by(self, queryset):
        return self.request.user.um_profile.items_per_page


class FeedList(LoginRequiredMixin, ListView):
    model = models.Feed
    ordering = 'created_at'

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(subscribers=self.request.user.reader_profile)
        )


class FeedDetailList(LoginRequiredMixin, ListView):
    model = models.Article
    template_name = 'reader/feed_detail_list.html'
    context_object_name = 'articles'

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(feed=self.kwargs.get('pk'))
            .prefetch_related('read_by', 'stared_by', 'feed')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feed'] = get_object_or_404(models.Feed,
                                            pk=self.kwargs.get('pk'))
        return context

    def get_paginate_by(self, queryset):
        return self.request.user.um_profile.items_per_page


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


class ReadAllView(LoginRequiredMixin, View):

    def post(self, request, pk=None):
        query = models.Article.objects
        if pk:
            query = query.filter(feed_id=pk)
        else:
            query = query.filter(
                feed__in=self.request.user.reader_profile.feeds.all()
            )
        articles = query.exclude(
            id__in=self.request.user.reader_profile.read.all()
        )
        request.user.reader_profile.read.add(*articles)
        return HttpResponse(status=204)
