from django.conf.urls import url

from . import views

app_name = 'collection'
urlpatterns = [
    url(r'^package/$', views.PackageListView.as_view(), name='index'),
    url(r'^package/$', views.PackageListView.as_view(), name='package_list'),
    url(r'^package/(?P<pk>[0-9]+)/$', views.PackageDetailView.as_view(), name='package_detail'),
    url(r'^package/(?P<pk>[0-9]+)/download/$', views.package_download, name='package_download'),
    url(r'^package/(?P<package_pk>[0-9]+)/image/(?P<pk>[0-9]+)/$', views.ImageDetailView.as_view(), name='image_detail'),
    url(r'^package/(?P<package_pk>[0-9]+)/image/(?P<pk>[0-9]+)/download/$', views.image_download, name='image_download'),
]
