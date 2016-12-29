from collection.models import Image, Package
from collection import filename_mapper
from character import settings
from django.db import transaction
from django.db.models import Count

from prompter import yesno
import os

@transaction.atomic
def run(*args):
    if len(args) != 1:
        print('Usage: python manage.py runscript make_image_packages --traceback --script-args <package_size>')
    assert(len(args) == 1)
    package_size = int(args[0])
    has_package_exist = Package.objects.count() > 0
    if not has_package_exist:
        print('Script make_first_package must be run first. (python manage.py runscript make_first_package --traceback)')
    assert(has_package_exist)
    direction_set = Image.objects.filter(package=None).values('direction').annotate(count_direction=Count('pk')).order_by('direction')
    for direction_obj in direction_set:
        direction  = direction_obj['direction']
        cnt = direction_obj['count_direction']
        print("direction %d, %d images => %d packages (%d have no package, %d ignored)" % (direction, int(cnt / package_size) * package_size, int(cnt / package_size), cnt, cnt % package_size))
    assert(yesno("confirm?"))
    for direction_obj in direction_set:
        direction  = direction_obj['direction']
        images = Image.objects.filter(package=None, direction=direction).order_by('number').values_list('pk', flat=True)
        cnt = 0
        if (len(images) >= package_size):
            for start in range(0, len(images) - package_size + 1, package_size):
                package = Package.objects.create(direction=direction)
                Image.objects.filter(pk__in=images[start:start + package_size]).update(package=package)
                cnt += 1
        assert(cnt == int(direction_obj['count_direction'] / package_size))
