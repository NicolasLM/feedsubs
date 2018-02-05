from django.urls import path

from . import views

app_name = 'um'
urlpatterns = [
    path('settings/account', views.AccountSettings.as_view(),
         name='settings-account'),
    path('settings/interface', views.InterfaceSettings.as_view(),
         name='settings-interface'),
    path('settings/email', views.EmailSettings.as_view(),
         name='settings-email'),
    path('settings/security', views.SecuritySettings.as_view(),
         name='settings-security'),
]
