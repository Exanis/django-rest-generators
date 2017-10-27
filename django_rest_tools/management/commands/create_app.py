import os
from django.core.management import BaseCommand, CommandError, call_command
from django.conf import settings


class Command(BaseCommand):
    @staticmethod
    def _create_base_app(name):
        call_command('startapp', name)

    @staticmethod
    def _manage_individual_directory(app, name, create=True):
        target_remove = os.path.join(settings.BASE_DIR, app, "%s.py" % name)
        target_create = os.path.join(settings.BASE_DIR, app, name)
        target_init = os.path.join(target_create, '__init__.py')
        if os.path.isfile(target_remove):
            os.remove(target_remove)
        if create:
            os.mkdir(target_create)
            open(target_init, 'w+').close()

    @staticmethod
    def _create_structure(name):
        Command._manage_individual_directory(name, 'models')
        Command._manage_individual_directory(name, 'tests')
        Command._manage_individual_directory(name, 'views', False)
        Command._manage_individual_directory(name, 'viewsets')
        Command._manage_individual_directory(name, 'serializers')
        target_urls = os.path.join(settings.BASE_DIR, name, 'urls.py')
        with open(target_urls, 'w+') as file:
            file.write('''from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from %s import viewsets


router = DefaultRouter()

urlpatterns = [
    url(r'^', include(router.urls))
]
''' % name)

    @staticmethod
    def _add_to_configs(name):
        if hasattr(settings, 'SETTING_FILE'):
            with open(settings.SETTING_FILE, 'r+') as file:
                content = file.read()
                file.seek(0)
                file.truncate()
                content = content.replace('INSTALLED_APPS = [', """INSTALLED_APPS = [
    '%s',""" % name)
                file.write(content)
        if hasattr(settings, 'URLS_FILE'):
            with open(settings.URLS_FILE, 'r+') as file:
                content = file.read()
                file.seek(0)
                file.truncate()
                content = content.replace('urlpatterns = [', '''urlpatterns = [
    url(r'^%s/1.0/', include('%s.urls')),''' % (name, name,))
                file.write(content)

    def add_arguments(self, parser):
        parser.add_argument('name', help='Application name')

    def handle(self, *args, **options):
        name = options['name']
        target_path = os.path.join(settings.BASE_DIR, name)
        if os.path.isdir(target_path):
            raise CommandError('App %s already exist' % name)
        Command._create_base_app(name)
        self._create_structure(name)
        self._add_to_configs(name)
