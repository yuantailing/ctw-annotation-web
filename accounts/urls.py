# The views used below are normally mapped in django.contrib.admin.urls.py
# This URLs file is used to provide a reliable view deployment for test purposes.
# It is also provided as a convenience to those who want to deploy these URLs
# elsewhere.

from django.conf.urls import url
from django.contrib.auth import views
from django.shortcuts import render

app_name = 'accounts'
urlpatterns = [
    url('^$', lambda request: render(request, 'accounts/index.html'), name='index'),
    url(r'^login/$', views.login, {'template_name': 'accounts/login.html', 'redirect_authenticated_user': True}, name='login'),
    url(r'^logout/$', views.logout, {'template_name': 'accounts/logged_out.html'}, name='logout'),
    url(r'^password_change/$', views.password_change, {'template_name': 'accounts/password_change_form.html', 'post_change_redirect': 'accounts:password_change_done'}, name='password_change'),
    url(r'^password_change/done/$', views.password_change_done, {'template_name': 'accounts/password_change_done.html'}, name='password_change_done'),
    url(r'^password_reset/$', views.password_reset, {'template_name': 'accounts/password_reset_form.html', 'email_template_name': 'accounts/password_reset_email.html', 'post_reset_redirect': 'accounts:password_reset_done'}, name='admin_password_reset'),
    url(r'^password_reset/done/$', views.password_reset_done, {'template_name': 'accounts/password_reset_done.html'}, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.password_reset_confirm, {'template_name': 'accounts/password_reset_confirm.html', 'post_reset_redirect': 'accounts:password_reset_complete'}, name='password_reset_confirm'),
    url(r'^reset/done/$', views.password_reset_complete, {'template_name': 'accounts/password_reset_done.html'}, name='password_reset_complete'),
]
