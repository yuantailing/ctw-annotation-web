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
        print 'Usage: python manage.py runscript make_image_packages --traceback --script-args <package_size>'
    assert(len(args) == 1)
    package_size = int(args[0])
    # direction_set = Image.objects.filter(package=None).values('direction').annotate(count_direction=Count('pk'))
    direction_set = Image.objects.raw("SELECT id, direction, COUNT(id) AS count_direction FROM collection_image GROUP BY direction")
    direction_set = list(direction_set)
    print direction_set
    # direction_set = filter(lambda d: d['count_direction'] >= package_size, direction_set)
    direction_set.sort(cmp=lambda a, b: 1 if a.direction > b.direction else -1)
    for direction_obj in direction_set:
        direction  = direction_obj.direction
        cnt = direction_obj.count_direction
        print "direction %d, %d images => %d packages (%d have no package, %d ignored)" % (direction, cnt / package_size * package_size, cnt / package_size, cnt, cnt % package_size)
    assert(yesno("confirm?"))
    for direction_obj in direction_set:
        direction  = direction_obj.direction
        images = Image.objects.filter(package=None, direction=direction).order_by('number').values_list('pk', flat=True)
        cnt = 0
        if (len(images) >= package_size):
            for start in xrange(0, len(images) - package_size + 1, package_size):
                package = Package.objects.create(direction=direction)
                Image.objects.filter(pk__in=images[start:start + package_size]).update(package=package)
                cnt += 1
        assert(cnt == direction_obj.count_direction / package_size)
