from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, FileResponse, StreamingHttpResponse, Http404
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.db.models import Count
from character import settings
from collection import filename_mapper
from .models import Image, Package, UserPackage
from .forms import UploadPackageFileForm
import zipfile
import time
import os
import io

# Create your views here.

def index(request):
    return redirect(reverse('collection:package_list'))


def package_list(request):
    userpackage_list = get_list_or_404(request.user.userpackage_set.select_related('package').annotate(Count('package__image')))
    return render(request, 'collection/package_list.html', {'userpackage_list': userpackage_list})


def package_detail(request, pk):
    userpackage = get_object_or_404(request.user.userpackage_set.select_related('package').annotate(Count('package__image')), package_id=pk)
    return render(request, 'collection/package_detail.html', {'userpackage': userpackage})


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


def annotation_download(request, pk):
    userpackage = get_object_or_404(request.user.userpackage_set.select_related('package'), package_id=pk)
    response = FileResponse(open(userpackage.upload.path, 'rb'))
    response['Content-Disposition'] = 'attachment;filename="%s.annotation.package"' % userpackage.package
    return response


def annotation_upload(request, pk):
    user_package = get_object_or_404(request.user.userpackage_set.all(), package__pk=pk)
    if request.method == 'POST':
        form = UploadPackageFileForm(request.POST, request.FILES)
        if form.is_valid():
            mem_file = request.FILES['annotations']
            formated_time = time.strftime('%Y-%m-%d-%H%M%S')
            ext = mem_file.name.split('.')[-1]
            mem_file.name = 'annotations-%d-%d.%s.%s' % (user_package.user_id, user_package.package_id, formated_time, ext)
            user_package.upload = mem_file
            user_package.save()
            return redirect(reverse('collection:package_detail', kwargs={'pk': pk}))
    else:
        form = UploadPackageFileForm()
    return render(request, 'collection/annotation_upload.html', {'package': user_package.package, 'form': form})


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


def tools_index(request):
    return render(request, 'collection/tools_index.html')
