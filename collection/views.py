from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, FileResponse, StreamingHttpResponse, Http404
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import models as auth_models

from django.db import transaction
from django.db.models import Count
from character import settings
from collection import filename_mapper
from .models import Image, Package, UserPackage
from .forms import UploadPackageFileForm
import zipfile
import subprocess
import base64
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
        with transaction.atomic():
            package = Package.objects.select_for_update().exclude(users__id__contains=request.user.id).annotate(Count('users')).filter(users__count__lt=2).order_by('-users__count', 'direction', 'id').first()
            if request.user.userpackage_set.filter(upload__isnull=True).count() != 0:
                return render(request, 'collection/ask_for_package.html', {'error_message': 'You forgot to upload annotations to some packages.'})
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
    statistics = json.loads(userpackage.statistics) if userpackage.statistics else dict() # todo: check json in scripts/collection_check
    feedback = json.loads(userpackage.feedback) if userpackage.feedback else dict()
    image_info = []
    num_image = 0
    num_block = 0
    num_character = 0
    num_error = 0
    num_miss = 0
    num_reduntant = 0
    character_cnt = 0
    character_pass = 0
    for image in userpackage.package.image_set.all():
        stat = statistics[image.get_distribute_name()] if image.get_distribute_name() in statistics else None
        feed = feedback[image.get_distribute_name()] if image.get_distribute_name() in feedback else None
        feeddisplay = None
        if feed:
            feeddisplay = dict()
            feeddisplay['error'] = len(feed['error'])
            feeddisplay['miss'] = len(feed['miss'])
            feeddisplay['reduntant'] = len(feed['reduntant'])
            thiscnt = (stat['numCharacter'] if stat else 0) + feeddisplay['miss']
            thispass = max(0, thiscnt - feeddisplay['error'] - feeddisplay['miss'] - feeddisplay['reduntant'])
            num_image += 1
            num_block += stat['numBlock'] if stat else 0
            num_character += stat['numCharacter'] if stat else 0
            num_error += feeddisplay['error']
            num_miss += feeddisplay['miss']
            num_reduntant += feeddisplay['reduntant']
            if thiscnt:
                feeddisplay['pass'] = '%.2f %%' % (thispass * 100.0 / thiscnt)
            else:
                feeddisplay['pass'] = '#DIV/0!'
        image_info.append({'id': image.id, 'title': image.__str__(), 'direction': image.direction, 'number': image.number, 'stat': stat, 'feed': feeddisplay})
    statcnt = num_character + num_miss
    statpass = max(0, statcnt - num_error - num_miss - num_reduntant)
    statistics = {'num_image': num_image, 'num_block': num_block, 'num_character': num_character, 'num_error': num_error, 'num_miss': num_miss, 'num_reduntant': num_reduntant,
        'workload': num_block * 2 + num_character,'pass': '%.2f %%' % (statpass * 100.0 / statcnt)} if num_character else None
    return render(request, 'collection/package_detail.html', {'userpackage': userpackage, 'image_info': image_info, 'statistics': statistics})


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
            raise ValueError("File %s not found. A server error occurred. Please contact the administrator." % filename[1])
    return response


@login_required
def annotation_download(request, pk):
    userpackage = get_object_or_404(request.user.userpackage_set.select_related('package'), package_id=pk)
    response = HttpResponse(userpackage.upload)
    response['Content-Disposition'] = 'attachment;filename="%s.annotation.pack"' % userpackage.package
    return response


@login_required
def annotation_upload(request, pk):
    if request.method == 'POST':
        form = UploadPackageFileForm(request.POST, request.FILES)
        if form.is_valid():
            mem_file = request.FILES['annotations']
            if mem_file.size > 3 * 1024 * 1024:
                return render(request, 'collection/annotation_upload.html', {'package': get_object_or_404(Package.objects, pk=pk), 'form': form, 'error_message': 'Files larger than 3MB are not accepted. If you annotations do exceed 3MB, please contact the administrator.'})
            mem_data = b''
            for chunk in mem_file.chunks():
                mem_data += chunk
            with transaction.atomic():
                locked_userpackages = UserPackage.objects.select_for_update().filter(package_id=pk)
                do_lock = len(locked_userpackages)
                userpackage = get_object_or_404(locked_userpackages, user_id=request.user.id)
                userpackage.upload = mem_data
                exe = os.path.join('..', 'imageviewer', 'dist', 'validation', 'validation')
                p = subprocess.Popen([exe, '-s'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                res, junk = p.communicate('%s\n' % base64.b64encode(userpackage.upload))
                p.wait()
                assert(p.returncode == 0)
                res = json.loads(res, encoding='utf-8')
                if (res["error"] != 0):
                    return render(request, 'collection/annotation_upload.html', {'package': userpackage.package, 'form': form, 'error_message': res["errorMessage"]})
                res = res["images"]
                statistics = dict()
                if False: # check image set
                    image_diff = set()
                    for image in userpackage.package.image_set.all():
                        image_diff.add(image.get_distribute_name())
                    for image in res:
                        if image not in image_diff:
                            return render(request, 'collection/annotation_upload.html', {'package': userpackage.package, 'form': form, 'error_message': 'Rejected: Image-%s is not in this package, but you uploaded it.' % image})
                        image_diff.remove(image)
                        statistics[image] = {'numBlock': res[image]['numBlock'], 'numCharacter': res[image]['numCharacter']}
                    if len(image_diff) != 0:
                        return render(request, 'collection/annotation_upload.html', {'package': userpackage.package, 'form': form, 'error_message': 'Rejected: Image-%s is in this package, but you didn\'t upload it.' % image_diff.pop()})
                else: # do not check image set
                    for image in res:
                        statistics[image] = {'numBlock': res[image]['numBlock'], 'numCharacter': res[image]['numCharacter']}
                userpackage.statistics = json.dumps(statistics)
                other = locked_userpackages.exclude(user_id=request.user.id).order_by('user_id').first()
                if other and other.upload:
                    p = subprocess.Popen([exe, '-r', '0.70'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                    res, junk = p.communicate('%s\n%s\n' % (base64.b64encode(userpackage.upload), base64.b64encode(other.upload)))
                    p.wait()
                    assert(p.returncode == 0)
                    res = json.loads(res, encoding='utf-8')
                    assert(res["error"] == 0)
                    userpackage.feedback = json.dumps(res["feedback1"])
                    other.feedback = json.dumps(res["feedback2"])
                    locked_userpackages.update(feedback='')
                    userpackage.save()
                    other.save()
                else:
                    userpackage.save()
                    locked_userpackages.update(feedback='')
                return redirect(reverse('collection:package_detail', kwargs={'pk': pk}))
    else:
        userpackage = get_object_or_404(request.user.userpackage_set, package_id=pk)
        form = UploadPackageFileForm()
    return render(request, 'collection/annotation_upload.html', {'package': userpackage.package, 'form': form})


@login_required
def feedback_download(request, pk):
    userpackage = get_object_or_404(request.user.userpackage_set.select_related('package'), package_id=pk)
    response = HttpResponse(userpackage.feedback)
    response['Content-Disposition'] = 'attachment;filename="%s.feedback.json"' % userpackage.package
    return response


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
