from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse, StreamingHttpResponse, Http404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from character import settings
from collection import filename_mapper
from .models import Image, Package
import zipfile
import os
import io

# Create your views here.

class PackageListView(LoginRequiredMixin, generic.ListView):
    def get_queryset(self):
        return self.request.user.package_set.all()


class PackageDetailView(LoginRequiredMixin, generic.DetailView):
    def get_queryset(self):
        return self.request.user.package_set.all()


@login_required
def package_download(request, pk):
    package = get_object_or_404(request.user.package_set.all(), pk=pk)
    def zip_iterator(file_list, compression=zipfile.ZIP_STORED):
        buffer = io.BytesIO()
        zf = zipfile.ZipFile(buffer, mode='w', compression=compression, allowZip64=False)
        last_write = buffer.tell()
        for tup in file_list:
            zf.write(*tup)
            current = buffer.tell()
            buffer.seek(last_write, 0)
            yield buffer.read(current - last_write)
            last_write = current
        zf.close()
        current = buffer.tell()
        if current != last_write:
            buffer.seek(last_write, 0)
            yield buffer.read(current - last_write)
        buffer.close()
    file_list = []
    for image in package.image_set.all():
        file_list.append((image.get_file_path(), image.get_distribute_name()))
    response = StreamingHttpResponse(zip_iterator(file_list))
    response['Content-Disposition'] = 'attachment;filename="%s.zip"' % package
    for filename in file_list:
        if not os.path.exists(filename[0]):
            raise ValueError("File %s not found. It may be a server filesystem issue. Please report this incident to administratior." % filename[1])
    return response


class ImageDetailView(LoginRequiredMixin, generic.DetailView):
    model = Image
    def get_queryset(self):
        package = get_object_or_404(self.request.user.package_set.all(), pk=self.kwargs['package_pk'])
        return package.image_set.all()


@login_required
def image_download(request, package_pk, pk):
    package = get_object_or_404(request.user.package_set.all(), pk=package_pk)
    image = get_object_or_404(package.image_set, pk=pk)
    response = FileResponse(open(image.get_file_path(), 'rb'))
    response['Content-Disposition'] = 'attachment;filename="%s.jpg"' % image.get_distribute_name()
    return response
