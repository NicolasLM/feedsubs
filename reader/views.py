from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, FormView
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from . import models, forms, tasks


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
    model = models.Subscription
    ordering = 'subscribed_at'
    template_name = 'reader/feed_list.html'

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(reader=self.request.user.reader_profile)
            .select_related('feed')
        )


class ExportFeedList(FeedList):
    template_name = 'reader/opml-export.xml'
    content_type = 'application/xml'

    def render_to_response(self, context, **response_kwargs):
        rv = super().render_to_response(context, **response_kwargs)
        rv['Content-Disposition'] = 'attachment; filename="feedsubs-export.xml"'
        return rv


class ImportFeedList(LoginRequiredMixin, FormView):
    template_name = 'reader/opml_import_form.html'
    form_class = forms.UploadOPMLFileForm
    success_url = reverse_lazy('reader:feed-list')

    def form_valid(self, form):
        tasks.import_feeds_from_opml_data(
            self.request.user.id,
            self.request.FILES['file'].read()
        )
        return super().form_valid(form)


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
        from . import forms
        context = super().get_context_data(**kwargs)
        context['feed'] = get_object_or_404(models.Feed,
                                            pk=self.kwargs.get('pk'))
        try:
            subscription = models.Subscription.objects.get(
                feed=self.kwargs.get('pk'),
                reader=self.request.user.reader_profile
            )
            context['subscription'] = subscription
            context['tag_form'] = forms.SubscriptionTagsForm(
                instance=subscription
            )
        except models.Subscription.DoesNotExist:
            context['subscription'] = None

        return context

    def get_paginate_by(self, queryset):
        return self.request.user.um_profile.items_per_page


class FeedCreate(LoginRequiredMixin, CreateView):
    model = models.Feed
    fields = ['uri']

    def form_valid(self, form):
        tasks.tasks.schedule('create_feed', self.request.user.id,
                             form.cleaned_data['uri'])
        return HttpResponseRedirect(self.get_success_url())

    def get_form(self, form_class=None):
        # Hack to prevent the form from failing when a feed with the same
        # uri already exists
        form = super().get_form(form_class)
        form.validate_unique = lambda: None
        return form

    def get_success_url(self):
        return reverse_lazy('reader:feed-list')


class SubscribeView(LoginRequiredMixin, View):

    def post(self, request, pk):
        feed = get_object_or_404(models.Feed, id=pk)
        subscription = models.Subscription(
            feed=feed, reader=self.request.user.reader_profile
        )
        subscription.save()
        return HttpResponse(status=204)


class UnsubscribeView(LoginRequiredMixin, View):

    def post(self, request, pk):
        reader_profile = request.user.reader_profile
        obj = get_object_or_404(
            models.Subscription, feed=pk, reader=reader_profile
        )
        obj.delete()
        return HttpResponse(status=204)


class UpdateSubscriptionTagsView(UpdateView):
    template_name = 'reader/feed_form.html'
    form_class = forms.SubscriptionTagsForm
    model = models.Subscription

    def get_object(self, queryset=None):
        return get_object_or_404(
            models.Subscription,
            feed=self.kwargs.get('pk'),
            reader=self.request.user.reader_profile,
        )

    def get_form(self, *args, **kwargs):
        # Hack to remove leading and tailing commas from tags-input
        post = self.request.POST.copy()
        post['tags'] = self.request.POST['tags'].strip(',').replace(',,', ',')
        self.request.POST = post
        return super().get_form(*args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('reader:feed-detail',
                            kwargs={'pk': self.kwargs.get('pk')})


class Starred(LoginRequiredMixin, ListView):
    model = models.Article
    template_name = 'reader/starred.html'
    context_object_name = 'articles'

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(stared_by=self.request.user.reader_profile)
            .prefetch_related('read_by', 'stared_by', 'feed')
        )

    def get_paginate_by(self, queryset):
        return self.request.user.um_profile.items_per_page


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
