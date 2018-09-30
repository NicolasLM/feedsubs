from django.urls import path

from . import views

app_name = 'reader'
urlpatterns = [
    path('feeds', views.FeedList.as_view(), name='feed-list'),
    path('feeds/export', views.ExportFeedList.as_view(), name='feed-export'),
    path('feeds/import', views.ImportFeedList.as_view(), name='feed-import'),
    path('feeds/new', views.FeedCreate.as_view(), name='feed-create'),

    path('feeds/<int:pk>', views.FeedDetailList.as_view(), name='feed-detail'),
    path('feeds/<int:pk>/subscribe', views.SubscribeView.as_view()),
    path('feeds/<int:pk>/unsubscribe', views.UnsubscribeView.as_view()),
    path('feeds/<int:pk>/tags', views.UpdateSubscriptionTagsView.as_view(),
         name='feed-update-tags'),
    path('feeds/<int:pk>/read-all', views.ReadAllView.as_view(),
         name='feed-read-all'),

    path('boards', views.BoardList.as_view(), name='board-list'),
    path('boards/new', views.BoardCreate.as_view(), name='board-create'),
    path('boards/<int:pk>', views.DBBoardDetailList.as_view(),
         name='board-detail'),
    path('boards/<int:pk>/edit', views.BoardUpdate.as_view(),
         name='board-update'),
    path('boards/<int:pk>/delete', views.BoardDelete.as_view(),
         name='board-delete'),
    path('boards/<int:pk>/read-all', views.DBReadAllBoard.as_view(),
         name='board-read-all'),

    path('articles/<int:pk>/star', views.StarArticleView.as_view(),
         name='star-article'),
    path('articles/<int:pk>/unstar', views.UnstarArticleView.as_view(),
         name='unstar-article'),
    path('articles/<int:pk>/read', views.ReadArticleView.as_view(),
         name='read-article'),
    path('articles/<int:pk>/unread', views.UnreadArticleView.as_view(),
         name='unread-article'),

    path('starred', views.Starred.as_view(), name='starred'),
    path('starred/read-all', views.StarredReadAllBoard.as_view(),
         name='starred-read-all'),

    path('read-all', views.AllReadAllBoard.as_view(),
         name='all-read-all'),
    path('fetcher', views.FetcherTemplate.as_view(), name='fetcher'),
    path('', views.home_router, name='home'),
]
