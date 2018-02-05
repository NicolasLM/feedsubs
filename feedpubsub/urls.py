"""feedpubsub URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from allauth.account.urls import urlpatterns as accounts_urlpatterns
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

accounts_urlpatterns_to_keep = {
    'account_signup', 'account_login', 'account_logout', 'account_inactive',
    'account_confirm_email', 'account_reset_password',
    'account_reset_password_done', 'account_reset_password_from_key',
    'account_reset_password_from_key_done'
}
accounts_urlpatterns = [u for u in accounts_urlpatterns
                        if u.name in accounts_urlpatterns_to_keep]


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(accounts_urlpatterns)),
    path('', include('reader.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
