from django.urls import path

from . import views

app_name = 'reader'
urlpatterns = [
    path('feeds', views.FeedList.as_view(), name='feed-list'),
    path('feeds/new', views.FeedCreate.as_view(), name='feed-create'),
    path('feeds/<int:pk>', views.FeedDetail.as_view(), name='feed-detail'),
    path('feeds/<int:pk>/unsubscribe', views.UnsubscribeView.as_view()),

    path('articles/<int:pk>/star', views.StarArticleView.as_view(),
         name='star-article'),
    path('articles/<int:pk>/unstar', views.UnstarArticleView.as_view(),
         name='unstar-article'),
    path('articles/<int:pk>/read', views.ReadArticleView.as_view(),
         name='read-article'),
    path('articles/<int:pk>/unread', views.UnreadArticleView.as_view(),
         name='unread-article'),

    path('settings/account', views.AccountSettings.as_view(),
         name='settings-account'),
    path('settings/interface', views.InterfaceSettings.as_view(),
         name='settings-interface'),
    path('settings/email', views.EmailSettings.as_view(),
         name='settings-email'),
    path('settings/security', views.SecuritySettings.as_view(),
         name='settings-security'),

    path('', views.Home.as_view(), name='home'),
]
