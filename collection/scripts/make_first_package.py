from collection.models import Image, Package
from collection import filename_mapper
from character import settings
from django.db import transaction
from django.db.models import Count

from prompter import yesno
import os

# Usage: python manage.py runscript make_first_package --traceback

@transaction.atomic
def run(*args):
    assert(Package.objects.count() == 0)
    direction = 3
    numbers = ['034026', '034134', '034251']
    package = Package.objects.create(direction=direction)
    for number in numbers:
        image, created = Image.objects.get_or_create(package=None, direction=direction, number=number)
        image.package = package
        image.save()

