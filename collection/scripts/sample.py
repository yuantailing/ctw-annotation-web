from collection.models import User

# Usage: python manage.py runscript sample --traceback --script-args staleonly

def run(*args):
    print args
    print User.objects.all()
    failed()
