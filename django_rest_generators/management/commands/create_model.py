import os
from django.core.management import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('app', help='Target application name')
        parser.add_argument('name', help='Target model name')

    def handle(self, *args, **options):
        app = options['app']
        name = options['name'].lower()
        target_path = os.path.join(
            settings.BASE_DIR,
            app,
            'models',
            '%s.py' % name
        )
        if os.path.isfile(target_path):
            raise CommandError('Model %s already exists in %s' % (name, app,))
        with open(target_path, 'w+') as file:
            file.write("""from uuid import uuid4
from django.db import models


class %s(models.Model):
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    
    class Meta(object):
        permissions = (
            ('view_%s', 'View %s',),
        )
        default_related_name = '%ss'
""" % (name.capitalize(), name, name, name))
        init_path = os.path.join(
            settings.BASE_DIR,
            app,
            'models',
            '__init__.py'
        )
        with open(init_path, 'a+') as file:
            file.write('''from .%s import %s
''' % (name, name.capitalize(),))
