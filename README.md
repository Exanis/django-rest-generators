# django-rest-tools
A set of tools used to make django models management faster with django-rest-framework and behave

## Install
Just as most of django tools, you can install DRT quite quickly :

``pip install django-rest-tools``

Then just add django_rest_tools to your INSTALLED_APPS

If you want to use auto-install for newly created application (recommanded), you should also add :

```python
SETTING_FILE = os.path.abspath(__file__)
URLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'urls.py')
```

somewhere in your settings.py file (or the same file where you put INSTALLED_APPS, if you use multiple files)

## Added commands

The following commands are added to your project when you use DRT :

### create_app

The ``create_app`` command take one parameter (name) and create a rest-ready application with this name :

```bash
$ python manage.py create_app my_app
```

The created application with be added to your project's urls with the following path :

``/my_app/1.0/``

The 1.0 part is intended to let you use it as an evolving API and is expected to be present in file genereted by ``make_rest_model`` command (see below)

### create_model

The ``create_model`` command take two parameters (app and name)
and create a rest-ready model with this name inside the application :

```bash
$ python manage.py create_model my_app my_model
```

### make_rest_model

The ``make_rest_model`` command is the main tool in DRT. It parse a model an generate a set of ready-to-use
tools around it :

- A serializer
- A viewset
- A gherkin test file
- A gherkin step to populate a mock-up database

By now, the following fields are understood :

- BooleanField
- NullBooleanField
- CharField
- TextField
- EmailField
- SlugField
- URLField
- UUIDField
- GenericIPAddressField
- IntegerField
- SmallIntegerField
- PositiveIntegerField
- PositiveSmallIntegerField
- FloatField
- DateTimeField
- DateField

Other fields may be present in the model, but they will not be included in the resulting serializer. Please also note
that related fields will not be included either - you must define your relations manually in your serializer.

You may also specify a given set of permissions to allow on your viewset by using``-p`` option.

```bash
$ python manage.py my_app my_model [-p permission]
```

The following permissions are availables:

name | description | create | list | detail | update | delete
-----|-------------|--------|------|--------|--------|-------
everyone | Allow everyone to do everything | Everyone | Everyone | Everyone | Everyone | Everyone
auth | Require login for every action | User | User | User | User | User
auth_or_read_only | Require login for modification only | User | Everyone | Everyone | User | User
model | Require global permission for everything | add_*model* | view_*model* | view_*model* | change_*model* | delete_*model*
model_or_read_only | Require global permissions for modification | add_*model* | User | User | change_*model* | delete_*model*
model_or_anon_read_only | Require global permissions for modification, everyone can read | add_*model* | Everyone | Everyone | change_*model* | delete_*model*
object | Require object permissions for everything | add_*model* | view_*model* | view_*model* | change_*model* | delete_*model*
object_or_read_only | Require object permissions for modification | add_*model* | User | User | change_*model* | delete_*model*
object_or_anon_read_only | Require object permissions for modification, everyone can read | add_*model* | Everyone | Everyone | change_*model* | delete_*model* 
admin | Require to be a staff member (is_staff=True) for every operations | Staff | Staff | Staff | Staff | Staff

By default, the ``everyone`` permission is set.

##### Global and object permissions

An important distinction exist between global permission and object-level permissions. Global permissions are given to
an user without object, as such :

```python
from guardian.shortcuts import assign_perms
from myapp import models

user = models.Users.objects.get(username='MyUser')
assign_perms('view_mymodel', user)
```

and object-level permissions are assigned to an user with a specific object, as such :

```python
from guardian.shortcuts import assign_perms
from myapp import models

user = models.Users.objects.get(username='MyUser')
target = models.MyObject.objects.get(pk=42)
assign_perms('view_mymodel', user, target)
```

When using object-level permissions, you must also give to the user the corresponding global permissions ; in other words,
this will not be enough :

```python
from guardian.shortcuts import assign_perms
from myapp import models

user = models.Users.objects.get(username='MyUser')
target = models.MyObject.objects.get(pk=42)
assign_perms('view_mymodel', user, target)
# If i try to access target with MyUser, I will face a 403 error
```

But this is enough and safe :

```python
from guardian.shortcuts import assign_perms
from myapp import models

user = models.Users.objects.get(username='MyUser')
target = models.MyObject.objects.get(pk=42)
assign_perms('view_mymodel', user)
assign_perms('view_mymodel', user, target)
# Now I can view my model
```

For obvious reasons, you only need global add_*model* permission to create an object, even with object-level permissions.

In the previous table, you must replace *model* by the name of your model. When creating a model, the following three permissions are created by Django :

- add_*model*
- change_*model*
- delete_*model*

DRT will assume a fourth permission exists if you use ``model`` or ``object`` permissions : view_*model*

## Other tools

DRT also add some shortcuts that may be usefull in some context and that can be used in your project.

### Gherkin sentences

To use DRT's gherkin sentences, you must include it in your steps definition. You can do so by adding the following line in the \_\_init__.py file in your ``steps`` directory :

```python
from django_rest_tools.steps import authentication, database, http
```

Here is the list of sentences :

##### Users and authentication

step | regexp | example | usage
----|-------|---------|-------
Given | i am logged in as (?P<username>[^ ]+) | i am logged in as *MyUser* |Simulate a login over the API
Given | i am not logged in |  | Do nothing (pass) ; this is useful to make your intention clear in your test file
Given | a basic set of users exists in the database | | Create three users in your database : administrator (with is_staff=True), allowed_user and unallowed_user
Given | a super administrator exists in the database | | Create a single super-user (is_staff=True, is_superuser=True) in your database with username superadmin
Given | user (?P<user>[^ ]+) have permission (?P<perm>[^ ]+) | user *MyUser* have permission *my_app.add_my_model* | Give a global permission to an user
Given | user (?P<user>[^ ]+) have permission (?P<perm>[^ ]+) over a (?P<model>[^ ]+) with (?P<key>[^ ]+) (?P<key_value>.+) | User *MyUser* have permission *my_app.change_my_model* over a *my_model* with *id* *2* | Give a specific object-level permission to an user. *Note*: This will not give the corresponding global permission to this user

##### Database

step | regexp | example | usage
-----|-------|---------|-------
Then | a (?P<model_name>[a-zA-Z0-9_.]+) exists with (?P<key>[a-zA-Z0-9_]+) (?P<value>.+) | a *my_app.my_model* exists with *id* *2* | Check if a given model exists in the database with a given key
Then | no (?P<model_name>[a-zA-Z0-9_.]+) exists with (?P<key>[a-zA-Z0-9_]+) (?P<value>.+) | no *my_app.my_model* exists with *id* *2* | Check that a given model does not exist in the database with a given key

##### HTTP requests and values

step | regexp | example | usage
-----|--------|---------|------
When | i prepare a request to (?P<location>[a-zA-Z0-9\-_/.]+) | i prepare a request to */my_app/1.0/my_model/* | Initialize a request over an API endpoint
When | i provide (?P<key>[a-zA-Z0-9\-_]+) (?P<value>.+) | i provide *name* *This is a name* | Set a parameter to use for the request
When | i send the request using (?P<method>POST GET PUT PATCH DELETE) | i send the request using POST | Send the request over the API with the corresponding HTTP verb
Then | the return code is (?P<code>[0-9]+) | the return code is *404* | Specify the return code for the request
Then | the return value for (?P<key>[a-zA-Z0-9\-_]+) is (?P<value>.+) | the return value for *name* is *Some name* | Specify an expected value in a returned json object
Then | the returned array contain (?P<cnt>[0-9]+) elements | the returned array contain *2* elements | Assuming that the response from the API was a json array, validate the number of returned elements
Then | the returned element (?P<line>[0-9]+) have a key named (?P<key>[a-zA-Z0-9_]+) with value (?P<value>.+) | the returned element *2* have a key named *name* with value *the name* | Assuming that the response from the API was a json array of objects, validate that at the given line, the object contain a given key with a given value
Then | there is no (?P<key>[a-zA-Z0-9\-_]+) in the returned object | there is no *name* is the returned object | Assuming that the response is a json object, validate that a given key is not present in this object
Then | the returned element (?P<line>[0-9]+) have no key named (?P<key>[a-zA-Z0-9\-_]+) | the returned element *2* have no key named *name | Assuming that the response is a json array of object, validate that the object at the given line have no key of the given name

#### Initialization

To be able to use most of those sentences, you must initialize your testing environment. The sentences assume two elements :

- You will logout after each test
- You will have in your behave context a apiContext key with a rest_framework.test.APIClient instance

Here is a sample environment.py to meet those requirements :

```python
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'my_project.settings'
django.setup()

from django.test.runner import DiscoverRunner
from django.test.testcases import TestCase
from rest_framework.test import APIClient


def before_all(context):
    context.test_runner = DiscoverRunner()
    context.test_runner.setup_test_environment()
    context.old_db_config = context.test_runner.setup_databases()
    context.apiClient = APIClient()


def after_all(context):
    context.test_runner.teardown_databases(context.old_db_config)
    context.test_runner.teardown_test_environment()


def before_scenario(context, _):
    context.test = TestCase()
    context.test.setUpClass()


def after_scenario(context, _):
    context.test.tearDownClass()
    context.apiClient.logout()
    del context.test
```

### Permissions

Three classes are added to RestFramework's permissions classes :

- *DjangoModelPermissionsWithRead* : Work just as *DjangoModelPermissions* from rest_framework except that a view_*model* permission is expected for read actions
- *DjangoObjectPermissionsWithRead* : Work just as *DjangoObjectPermissions* from rest_framework except that a view_*model* permission is expected for read actions
- *DjangoObjectPermissionsOrAnonReadOnly* : Work just as *DjangoObjectPermissions* from rest_framework except that anonymous user is allowed to read actions as well

## Dependencies

DRT is strongly dependent of [DjangoRestFramework](http://www.django-rest-framework.org/) and [DjangoGuardian](https://github.com/django-guardian/django-guardian). It also need [Behave](https://pythonhosted.org/behave/).