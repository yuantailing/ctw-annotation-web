from collection.models import User

# Usage: python manage.py runscript sample --traceback --script-args staleonly

@transaction.atomic
def run(*args):
    print(args)
    print(User.objects.all())
    failed()
