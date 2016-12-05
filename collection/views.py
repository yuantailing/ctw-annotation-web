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
import subprocess
import json
import time
import os
import io

# Create your views here.

def index(request):
    return redirect(reverse('collection:package_list'))


@login_required
def ask_for_package(request):
    if request.method == 'POST':
        if request.user.userpackage_set.filter(upload='').count():
            return render(request, 'collection/ask_for_package.html', {'error_message': 'You forgot to upload annotations to some packages.'})
        package = Package.objects.select_for_update().exclude(users__id__contains=request.user.id).annotate(Count('users')).filter(users__count__lt=2).order_by('-users__count', 'direction', 'id').first()
        if not package:
            return render(request, 'collection/ask_for_package.html', {'error_message': 'No package avaliable, please contact the administrator.'})
        UserPackage.objects.create(user=request.user, package=package)
        return redirect(reverse('collection:package_list'))
    else:
        return render(request, 'collection/ask_for_package.html', {'error_message': None})


@login_required
def package_list(request):
    userpackage_list = request.user.userpackage_set.select_related('package').annotate(Count('package__image'))
    return render(request, 'collection/package_list.html', {'userpackage_list': userpackage_list})


@login_required
def package_detail(request, pk):
    userpackage = get_object_or_404(request.user.userpackage_set.select_related('package').annotate(Count('package__image')), package_id=pk)
    validation = json.loads(userpackage.validation) if userpackage.validation else dict() # todo: check json in scripts/collection_check
    image_info = []
    character_cnt = 0
    character_pass = 0
    for image in userpackage.package.image_set.all():
        info = validation[image.get_distribute_name()] if image.get_distribute_name() in validation else dict()
        if 'numBlock' not in info: info['numBlock'] = None
        if 'numCharacter' not in info: info['numCharacter'] = None
        if 'error' not in info or 'miss' not in info or 'reduntant' not in info:
            info['hasCross'] = False
            info['error'] = info['miss'] = info['reduntant'] = None
            thispass = None
        else:
            info['hasCross'] = True
            character_cnt += info['numCharacter'] or 0
            thispass = max(0, (info['numCharacter'] or 0) - (info['error'] or 0) - (info['miss'] or 0) - (info['reduntant'] or 0))
            character_pass += thispass
            if info['numCharacter']:
                thispass = '%.2f %%' % thispass * 100.0 / info['numCharacter']
            else:
                thispass = '-'
        image_info.append({'id': image.id, 'title': image.__str__(), 'direction': image.direction, 'number': image.number, 'numBlock': info['numBlock'], 'numCharacter': info['numCharacter'],
            'hasCross': info['hasCross'], 'error': info['error'], 'miss': info['miss'], 'reduntant': info['reduntant'], 'pass': thispass})
    return render(request, 'collection/package_detail.html', {'userpackage': userpackage, 'image_info': image_info})


@login_required
def package_download(request, pk):
    package = get_object_or_404(request.user.package_set, pk=pk)
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
        file_list.append((image.get_file_path(), '%s.jpg' % image.get_distribute_name()))
    response = StreamingHttpResponse(zip_iterator(file_list))
    response['Content-Disposition'] = 'attachment;filename="%s.zip"' % package
    for filename in file_list:
        if not os.path.exists(filename[0]):
            raise ValueError("File %s not found. It may be a server filesystem issue. Please report this incident to administratior." % filename[1])
    return response


@login_required
def annotation_download(request, pk):
    userpackage = get_object_or_404(request.user.userpackage_set.select_related('package'), package_id=pk)
    response = FileResponse(open(userpackage.upload.path, 'rb'))
    response['Content-Disposition'] = 'attachment;filename="%s.annotation.package"' % userpackage.package
    return response


@login_required
def annotation_upload(request, pk):
    userpackage = get_object_or_404(request.user.userpackage_set.select_for_update(), package_id=pk)
    if request.method == 'POST':
        form = UploadPackageFileForm(request.POST, request.FILES)
        if form.is_valid():
            mem_file = request.FILES['annotations']
            formated_time = time.strftime('%Y-%m-%d-%H%M%S')
            ext = 'package'
            mem_file.name = 'annotations-%d-%d.%s.%s' % (userpackage.user_id, userpackage.package_id, formated_time, ext)
            userpackage.upload = mem_file
            userpackage.save()
            other = UserPackage.objects.filter(package_id=pk).exclude(user_id=request.user.id).order_by('user_id').first()
            if other == None:
                exe = os.path.join('..', 'imageviewer', 'dist', 'validation', 'validation')
                p = subprocess.Popen([exe, '-s', userpackage.upload.path], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                p.stdin.close()
                res = ''
                while True:
                    more = p.stdout.read()
                    if (more == ''): break
                    res += more
                p.wait()
                assert(p.returncode == 0)
                res += p.stdout.read()
                res = json.loads(res)
                assert(res["error"] == 0)
                res = res["images"];
                validation = dict()
                for image in res:
                    validation[image] = {'numBlock': res[image]['numBlock'], 'numCharacter': res[image]['numCharacter']}
                userpackage.validation = json.dumps(validation)
                userpackage.save()
            return redirect(reverse('collection:package_detail', kwargs={'pk': pk}))
    else:
        form = UploadPackageFileForm()
    return render(request, 'collection/annotation_upload.html', {'package': userpackage.package, 'form': form})


class ImageDetailView(LoginRequiredMixin, generic.DetailView):
    model = Image
    def get_queryset(self):
        package = get_object_or_404(self.request.user.package_set, pk=self.kwargs['package_pk'])
        return package.image_set


@login_required
def image_download(request, package_pk, pk):
    package = get_object_or_404(request.user.package_set, pk=package_pk)
    image = get_object_or_404(package.image_set, pk=pk)
    response = FileResponse(open(image.get_file_path(), 'rb'))
    response['Content-Disposition'] = 'attachment;filename="%s.jpg"' % image.get_distribute_name()
    return response


def help(request):
    return render(request, 'collection/help.html')
