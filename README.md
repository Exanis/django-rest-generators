# django-rest-tools
A set of tools used to make django models management faster with django-rest-framework and behave

## Install
Just as most of django tools, you can install DRT quite quickly :

``pip install django-rest-tools``

Then just add django_rest_tools to your INSTALLED_APPS

If you want to use auto-install for newly created application (recommanded), you should also add :

``SETTING_FILE = os.path.abspath(__file__)
URLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'urls.py')``

somewhere in your settings.py file (or the same file where you put INSTALLED_APPS, if you use multiple files)

## Added commands

The following commands are added to your project when you use DRT :

### create_app

The ``create_app`` command take one parameter (name) and create a rest-ready application with this name

### create_model

The ``create_model`` command take two parameters (app and name)
and create a rest-ready model with this name inside the application