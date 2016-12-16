from collection.models import Image
from collection import filename_mapper
from character import settings
from django.db import transaction

import os

@transaction.atomic
def run(*args):
    if len(args) != 3:
        print('Usage: python manage.py runscript add_images --traceback --script-args <direction> <lo> <hi>')
    assert(len(args) == 3)
    direction = int(args[0])
    lo = int(args[1])
    hi = int(args[2])
    assert(lo < hi)
    folder = os.path.join(settings.IMAGE_DATA_ROOT, str(direction))
    ls_folder = os.listdir(folder)
    ls_folder = filter(lambda s: s.lower().endswith('.jpg'), ls_folder)
    ls_folder = map(lambda s: filename_mapper.mapper.old2new[s.split('.')[0]], ls_folder)
    ls_folder.sort()
    for number in ls_folder[lo:hi]:
        image, created = Image.objects.get_or_create(direction=direction, number=number)
        if created:
            print("[ OK ]\t%d\t%s" % (direction, number))
        else:
            print("[SKIP]\t%d\t%s" % (direction, number))
