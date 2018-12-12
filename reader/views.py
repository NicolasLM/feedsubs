from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    ListView, CreateView, UpdateView, FormView, DeleteView, TemplateView
)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.functional import cached_property
from spinach import Batch

from . import models, forms, tasks, static_boards, caching


def home_router(request):
    """Route request to the correct home view.

    Since the homepage is completely different if the user is anonymous, new or
    not, this function routes the request to the corresponding view.
    """
    if not request.user.is_authenticated:
        return render(request, 'reader/home_anonymous.html')

    has_subscription = models.Subscription.objects.filter(
        reader=request.user.reader_profile
    ).exists()
    if not has_subscription:
        return render(request, 'reader/home_new_user.html')

    return AllArticles.as_view()(request)


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


class ImportFeedList(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = 'reader/opml_import_form.html'
    form_class = forms.UploadOPMLFileForm
    success_url = reverse_lazy('reader:feed-list')
    success_message = ('The %d feeds found in the OPML file are being imported '
                       'in the background, they will be available shortly.')

    def form_valid(self, form):
        batch = Batch()
        for uri in form.cleaned_data['opml_uris']:
            batch.schedule('create_feed', self.request.user.id, uri)
        tasks.tasks.schedule_batch(batch)
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return self.success_message % len(cleaned_data['opml_uris'])


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
            .prefetch_related('read_by', 'stared_by', 'feed', 'attachment_set')
        )

    def get_context_data(self, **kwargs):
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

        context['cleaned_articles'] = caching.get_cleaned_articles(
            context['articles']
        )
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


class UpdateSubscriptionTagsView(LoginRequiredMixin, UpdateView):
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
                feed__subscribers=self.request.user.reader_profile
            )
        articles = query.exclude(
            read_by=self.request.user.reader_profile
        )
        request.user.reader_profile.read.add(*articles)
        return HttpResponse(status=204)


class BoardList(LoginRequiredMixin, ListView):
    model = models.Board
    template_name = 'reader/board_list.html'

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return static_boards.get_boards_for_user(self.request.user)


class BoardCreate(LoginRequiredMixin, CreateView):
    template_name = 'reader/board_form.html'
    model = models.Board
    form_class = forms.BoardForm
    success_url = reverse_lazy('reader:board-list')

    def form_valid(self, form):
        form.instance.reader = self.request.user.reader_profile
        return super().form_valid(form)


class BoardUpdate(LoginRequiredMixin, UpdateView):
    template_name = 'reader/board_form.html'
    model = models.Board
    form_class = forms.BoardForm
    success_url = reverse_lazy('reader:board-list')

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model,
            id=self.kwargs.get('pk'),
            reader=self.request.user.reader_profile,
        )


class BoardDelete(LoginRequiredMixin, DeleteView):
    model = models.Board
    success_url = reverse_lazy('reader:board-list')

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model,
            id=self.kwargs.get('pk'),
            reader=self.request.user.reader_profile,
        )


class BaseBoardDetailList(LoginRequiredMixin, ListView):
    model = models.Article
    template_name = 'reader/board_detail_list.html'
    context_object_name = 'articles'
    default_show_read = False
    empty_icon = 'fa-thumbs-up'
    empty_phrase = "You're all caught up"

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def board(self):
        raise NotImplementedError()

    @cached_property
    def mark_all_read_url(self):
        raise NotImplementedError()

    @cached_property
    def show_read(self):
        param = (
            self.kwargs.get('show-read') or self.request.GET.get('show-read')
        )
        if param is None:
            return self.default_show_read

        return param == 'true'

    def get_queryset(self):
        queryset = self.filter_queryset(super().get_queryset())
        if not self.show_read:
            queryset = queryset.exclude(
                read_by=self.request.user.reader_profile
            )
        return queryset.prefetch_related(
            'read_by', 'stared_by', 'feed', 'attachment_set'
        )

    def filter_queryset(self, queryset):
        raise NotImplementedError()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_boards = static_boards.get_boards_for_user(self.request.user)
        context['other_boards'] = [b for b in all_boards
                                   if b.pk != self.board.pk]
        context['show_read'] = self.show_read
        context['board'] = self.board
        context['empty_icon'] = self.empty_icon
        context['empty_phrase'] = self.empty_phrase
        context['mark_all_read_url'] = self.mark_all_read_url
        context['cleaned_articles'] = caching.get_cleaned_articles(
            context['articles']
        )
        return context

    def get_paginate_by(self, queryset):
        return self.request.user.um_profile.items_per_page


class DBBoardDetailList(BaseBoardDetailList):

    @cached_property
    def board(self):
        return get_object_or_404(
            models.Board,
            id=self.kwargs.get('pk'),
            reader=self.request.user.reader_profile,
        )

    @cached_property
    def mark_all_read_url(self):
        return reverse('reader:board-read-all',
                       kwargs={'pk': self.kwargs['pk']})

    def filter_queryset(self, queryset):
        subs = (
            models.Subscription.objects
            .filter(reader=self.request.user.reader_profile)
            .filter(tags__overlap=self.board.tags)
            .all()
        )
        feeds_id = [s.feed_id for s in subs]
        return queryset.filter(feed__in=feeds_id)


class AllArticles(BaseBoardDetailList):

    @cached_property
    def board(self):
        return static_boards.static_boards['all']

    @cached_property
    def mark_all_read_url(self):
        return reverse('reader:all-read-all')

    def filter_queryset(self, queryset):
        return queryset.filter(
            feed__subscribers=self.request.user.reader_profile
        )


class Starred(BaseBoardDetailList):
    default_show_read = True
    empty_icon = 'fa-star-half'
    empty_phrase = "No starred articles"

    @cached_property
    def board(self):
        return static_boards.static_boards['starred']

    @cached_property
    def mark_all_read_url(self):
        return reverse('reader:starred-read-all')

    def filter_queryset(self, queryset):
        return queryset.filter(stared_by=self.request.user.reader_profile)


class ReadAllBoard(LoginRequiredMixin, View):
    board_class_view = BaseBoardDetailList

    def post(self, request, pk=None):
        kwargs = {'pk': pk}
        board_view = self.board_class_view(request=request, kwargs=kwargs)
        queryset = models.Article.objects
        queryset = board_view.filter_queryset(queryset)
        articles = queryset.exclude(
            read_by=self.request.user.reader_profile
        )
        request.user.reader_profile.read.add(*articles)
        return HttpResponse(status=204)


class DBReadAllBoard(ReadAllBoard):
    board_class_view = DBBoardDetailList


class AllReadAllBoard(ReadAllBoard):
    board_class_view = AllArticles


class StarredReadAllBoard(ReadAllBoard):
    board_class_view = Starred


class FetcherTemplate(TemplateView):
    template_name = 'reader/fetcher.html'
