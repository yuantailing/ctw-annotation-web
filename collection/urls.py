from django.conf.urls import url

from . import views

app_name = 'collection'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^ask_for_package/$', views.ask_for_package, name='ask_for_package'),
    url(r'^package/$', views.package_list, name='package_list'),
    url(r'^package/(?P<pk>[0-9]+)/$', views.package_detail, name='package_detail'),
    url(r'^package/(?P<pk>[0-9]+)/download/$', views.package_download, name='package_download'),
    url(r'^package/(?P<pk>[0-9]+)/annotation/download/$', views.annotation_download, name='annotation_download'),
    url(r'^package/(?P<pk>[0-9]+)/annotation/upload/$', views.annotation_upload, name='annotation_upload'),
    url(r'^package/(?P<package_pk>[0-9]+)/image/(?P<pk>[0-9]+)/$', views.ImageDetailView.as_view(), name='image_detail'),
    url(r'^package/(?P<package_pk>[0-9]+)/image/(?P<pk>[0-9]+)/download/$', views.image_download, name='image_download'),
    url(r'^help/$', views.help, name='help'),
]
