from collection.models import Image
from collection import filename_mapper
from character import settings
from django.db import transaction

import os

# Usage: python manage.py runscript collection_check --traceback

@transaction.atomic
def run(*args):
    pass
