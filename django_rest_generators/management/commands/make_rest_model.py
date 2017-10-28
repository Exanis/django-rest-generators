import os
from django.core.management import BaseCommand
from django.db import models
from django.apps import apps
from django.conf import settings
from django_rest_generators import generators


class Command(BaseCommand):
    include_validators = False
    validators = []
    model = None
    model_name = ''
    read_only = []

    mapper_generators = {
        models.BooleanField: generators.boolean_generator,
        models.NullBooleanField: generators.boolean_generator,
        models.CharField: generators.text_generator,
        models.TextField: generators.text_generator,
        models.EmailField: generators.email_generator,
        models.SlugField: generators.slug_generator,
        models.URLField: generators.url_generator,
        models.UUIDField: generators.uuid_generator,
        models.GenericIPAddressField: generators.ip_generator,
        models.IntegerField: generators.integer_generator,
        models.SmallIntegerField: generators.integer_generator,
        models.PositiveIntegerField: generators.integer_generator,
        models.PositiveSmallIntegerField: generators.integer_generator,
        models.FloatField: generators.float_generator,
        models.DateTimeField: generators.datetime_generator,
        models.DateField: generators.date_generator
    }

    def __init__(self):
        super(Command, self).__init__()
        self.mapper_serializers = {
            models.BooleanField: lambda prop: self._generate_serialized(prop, "BooleanField"),
            models.NullBooleanField: lambda prop: self._generate_serialized(prop, "NullBooleanField"),
            models.CharField: lambda prop: self._generate_serialized(prop, "CharField", [
                "max_length=%s" % prop.max_length
            ]),
            models.TextField: lambda prop: self._generate_serialized(prop, "CharField"),
            models.EmailField: lambda prop: self._generate_serialized(prop, "EmailField"),
            models.SlugField: lambda prop: self._generate_serialized(prop, "SlugField"),
            models.URLField: lambda prop: self._generate_serialized(prop, "URLField"),
            models.UUIDField: lambda prop: self._generate_serialized(prop, "UUIDField", [
                "format='hex'"
            ]),
            models.GenericIPAddressField: lambda prop: self._generate_serialized(prop, "IPAdressField"),
            models.IntegerField: lambda prop: self._generate_serialized(prop, "IntegerField"),
            models.SmallIntegerField: lambda prop: self._generate_serialized(prop, "IntegerField", [
                "max_value=32767",
                "min_value=-32768"
            ]),
            models.PositiveIntegerField: lambda prop: self._generate_serialized(prop, "IntegerField", [
                "min_value=0"
            ]),
            models.PositiveSmallIntegerField: lambda prop: self._generate_serialized(prop, "IntegerField", [
                "max_value=32767",
                "min_value=0"
            ]),
            models.FloatField: lambda prop: self._generate_serialized(prop, "FloatField"),
            models.DateTimeField: lambda prop: self._generate_serialized(prop, "DateTimeField"),
            models.DateField: lambda prop: self._generate_serialized(prop, "DateField"),
        }

    def _import_model(self, app, name):
        self.model = apps.get_model(app, name)
        self.model_name = self.model._meta.model_name.capitalize()

    def _date_validator(self, validator, prop_name, prop_date):
        self.include_validators = True
        return """
            validators.%sValidator(
                queryset=models.%s.objects.all(),
                field='%s',
                date_field='%s'
            )""" % (
                validator,
                self.model_name,
                prop_name,
                prop_date
            )

    def _validators(self, prop):
        if prop.unique_for_month:
            self.validators.append(self._date_validator(
                'UniqueForMonth',
                prop.name,
                prop.unique_for_month
            ))
        elif prop.unique_for_year:
            self.validators.append(self._date_validator(
                'UniqueForYear',
                prop.name,
                prop.unique_for_year
            ))
        elif prop.unique_for_date:
            self.validators.append(self._date_validator(
                'UniqueForDate',
                prop.name,
                prop.unique_for_date
            ))

    def _common_props(self, prop):
        if not prop.editable:
            self.read_only.append(prop.name)
        basics = [
            "read_only=%s" % ("False" if prop.editable else "True"),
            "required=%s" % ("False" if prop.blank or not prop.editable else "True"),
            "allow_null=%s" % ("True" if prop.null else "False")
        ]
        if prop.unique:
            self.include_validators = True
            basics.append("""validators=[
            validators.UniqueValidator(
                queryset=models.%s.objects.all()
            )
        ]""" % self.model_name)
        return basics

    def _generate_serialized(self, prop, serializer, args=None):
        if args is None:
            args = []
        args += self._common_props(prop)
        return """%s = serializers.%s(
        %s
    )""" % (
            prop.name,
            serializer,
            ",\n        ".join(args)
        )

    def _map_properties(self):
        mapped = {
            'serialized': [],
            'fields': [],
            'test_generators': {},
            'test_required': [],
            'lookup_field': ''
        }
        for prop in self.model._meta.get_fields():
            if type(prop) in self.mapper_serializers:
                mapped['fields'].append(prop.name)
                self._validators(prop)
                mapped['serialized'].append(
                    self.mapper_serializers[type(prop)](prop)
                )
                mapped['test_generators'][prop.name] = \
                    self.mapper_generators[type(prop)]
                if prop.primary_key:
                    mapped['lookup_field'] = prop.name
                if not prop.blank:
                    mapped['test_required'].append(prop.name)
        return mapped

    def _generate_serializer(self, app, name, mapped):
        path = os.path.join(
            settings.BASE_DIR,
            app,
            "serializers",
            "%s.py" % name
        )
        init_path = os.path.join(
            settings.BASE_DIR,
            app,
            "serializers",
            "__init__.py"
        )
        with open(path, "w+") as file:
            file.write("""from rest_framework import serializers%s
from %s import models


class %s(serializers.ModelSerializer):
    %s
    
    class Meta(object):
        lookup_field = '%s'
        model = models.%s
        fields = (
            '%s'
        )%s
""" % (
                ", validators" if self.include_validators else '',
                app,
                name.capitalize(),
                "\n    ".join(mapped['serialized']),
                mapped['lookup_field'],
                name.capitalize(),
                "',\n            '".join(mapped['fields']),
                "" if len(self.validators) == 0 else """
        validators = [%s
        ]""" % ",".join(self.validators)
            ))
        with open(init_path, "a+") as file:
            file.write("from .%s import %s\n" % (name, name.capitalize(),))

    @staticmethod
    def _generate_testing_values(mapped, key, show_all=True):
        return ",\n        ".join([
            "%s='%s'" % (
                element,
                mapped['test_generators'][element](key)
            ) for element in mapped['fields']
            if element in mapped['test_required'] or show_all
        ])

    def _generate_behavior_maker(self, app, name, mapped):
        root = os.path.join(settings.BASE_DIR, "features")
        if not os.path.isdir(root):
            os.mkdir(root)
        steps = os.path.join(root, "steps")
        if not os.path.isdir(steps):
            os.mkdir(steps)
            init = os.path.join(steps, "__init__.py")
            with open(init, "w+") as file:
                file.write("from django_rest_generators.steps"
                           " import authentication, database, http\n")
        path = os.path.join(steps, "%s.%s.py" % (app, name))
        with open(path, "w+") as file:
            file.write("""from behave import use_step_matcher, given
from {0}.models import {1}


use_step_matcher('re')


@given(r'a basic set of {2} exists in the database')
def given_a_basic_set_of_{2}_exists(context):
    {1}.objects.create(
        {3}
    )
    {1}.objects.create(
        {4}
    )
""".format(
                app,
                self.model_name,
                name,
                Command._generate_testing_values(mapped, "First"),
                Command._generate_testing_values(mapped, "Second", False)
            ))

    def _generate_behavior_tests(self, app, name, mapped):
        path = os.path.join(
            settings.BASE_DIR,
            "features",
            "%s.%s.feature" % (app, name)
        )
        with open(path, "w+") as file:
            file.write("""# Created by Django Rest Generators
Feature: {0} management and persistance
  As autorized user,
  I want to be able to create a {1}, persiste it and retrieve it

  Scenario: Create a {1}
    Given a super administrator exists in the database
      And i am logged in as superadmin
    When i prepare a request to /{2}/1.0/{1}/
      {6}
      And i send the request using POST
    Then the return code is 201
      {10}

  Scenario: Create a {1} without required elements
    Given a super administrator exists in the database
      And i am logged in as superadmin
    When i prepare a request to /{2}/1.0/{1}/
      And i send the request using POST
    Then the return code is 400

  Scenario: Retrieve a {1}
    Given a super administrator exists in the database
      And i am logged in as superadmin
      And a basic set of {1} exists in the database
    When i prepare a request to /{2}/1.0/{1}/{5}/
      And i send the request using GET
    Then the return code is 200
      {10}

  Scenario: Retrieve an invalid {1}
    Given a super administrator exists in the database
      And i am logged in as superadmin
      And a basic set of {1} exists in the database
    When i prepare a request to /{2}/1.0/{1}/{4}/
      And i send the request using GET
    Then the return code is 404

  Scenario: List {1}s
    Given a super administrator exists in the database
      And i am logged in as superadmin
      And a basic set of {1} exists in the database
    When i prepare a request to /{2}/1.0/{1}/
      And i send the request using GET
    Then the return code is 200
      And the returned array contain 2 elements
      {8}
      {9}

  Scenario: List an empty set of {1}s
    Given a super administrator exists in the database
      And i am logged in as superadmin
    When i prepare a request to /{2}/1.0/{1}/
      And i send the request using GET
    Then the return code is 200
      And the returned array contain 0 elements

  Scenario: Update a {1}
    Given a super administrator exists in the database
      And i am logged in as superadmin
      And a basic set of {1} exists in the database
    When i prepare a request to /{2}/1.0/{1}/{5}/
      {12}
      And i send the request using PUT
    Then the return code is 200
        {14}
        {15}

  Scenario: Update an invalid {1}
    Given a super administrator exists in the database
      And i am logged in as superadmin
      And a basic set of {1} exists in the database
    When i prepare a request to /{2}/1.0/{1}/{4}/
      {6}
      And i send the request using PUT
    Then the return code is 404

  Scenario: Update a {1} without required elements
    Given a super administrator exists in the database
      And i am logged in as superadmin
      And a basic set of {1} exists in the database
    When i prepare a request to /{2}/1.0/{1}/{3}/
      And i send the request using PUT
    Then the return code is 400

  Scenario: Delete a {1}
    Given a super administrator exists in the database
      And i am logged in as superadmin
      And a basic set of {1} exists in the database
    When i prepare a request to /{2}/1.0/{1}/{5}/
      And i send the request using DELETE
    Then the return code is 204
      And no {2}.{1} exists with uuid {5}

  Scenario: Delete a non-existing {1}
    Given a super administrator exists in the database
      And i am logged in as superadmin
    When i prepare a request to /{2}/1.0/{1}/{4}/
      And i send the request using DELETE
    Then the return code is 404
""".format(
                self.model_name,
                name,
                app,
                mapped['test_generators'][mapped['lookup_field']]('Second'),
                mapped['test_generators'][mapped['lookup_field']]('Third'),
                mapped['test_generators'][mapped['lookup_field']]('First'),
                "\n      ".join([
                    "And i provide %s %s" % (
                        field,
                        mapped['test_generators'][field]('First')
                    ) for field in mapped['fields']
                    if field not in self.read_only
                ]),
                "\n      ".join([
                    "And i provide %s %s" % (
                        field,
                        mapped['test_generators'][field]('Second')
                    ) for field in mapped['fields']
                    if field in mapped['test_required']
                    and field not in self.read_only
                ]),
                "\n      ".join([
                    "And the returned element 0 have a key named %s with value %s" % (
                        field,
                        mapped['test_generators'][field]('First')
                    ) for field in mapped['fields']
                ]),
                "\n      ".join([
                    "And the returned element 1 have a key named %s with value %s" % (
                        field,
                        mapped['test_generators'][field]('Second')
                    ) for field in mapped['fields']
                    if field in mapped['test_required']
                ]),
                "\n      ".join([
                    "And the return value for %s is %s" % (
                        field,
                        mapped['test_generators'][field]('First')
                    ) for field in mapped['fields']
                    if field != mapped['lookup_field']
                ]),
                "\n      ".join([
                    "And the return value for %s is %s" % (
                        field,
                        mapped['test_generators'][field]('Second')
                    ) for field in mapped['fields']
                    if field in mapped['test_required']
                ]),
                "\n      ".join([
                    "And i provide %s %s" % (
                        field,
                        mapped['test_generators'][field]('Update')
                    ) for field in mapped['fields']
                    if field not in self.read_only
                ]),
                "\n      ".join([
                    "And i provide %s %s" % (
                        field,
                        mapped['test_generators'][field]('Update')
                    ) for field in mapped['fields']
                    if field in mapped['test_required']
                    and field not in self.read_only
                ]),
                "\n      ".join([
                    "And no %s.%s exists with %s %s" % (
                        app,
                        self.model_name,
                        field,
                        mapped['test_generators'][field]('First')
                    ) for field in mapped['fields']
                    if field not in self.read_only
                ]),
                "\n      ".join([
                    "And a %s.%s exists with %s %s" % (
                        app,
                        self.model_name,
                        field,
                        mapped['test_generators'][field]('Update')
                    ) for field in mapped['fields']
                    if field not in self.read_only
                ])
            ))

    def _generate_viewset(self, app, name, mapped, perms):
        viewset_path = os.path.join(
            settings.BASE_DIR,
            app,
            "viewsets"
        )
        viewset_file = os.path.join(viewset_path, "%s.py" % name)
        viewset_init = os.path.join(viewset_path, "__init__.py")
        drf_import = ''
        drg_import = ''
        if perms == "everyone":
            perms_classes = 'AllowAny'
            drf_import = ', permissions'
        elif perms == 'auth':
            perms_classes = 'IsAuthenticated'
            drf_import = ', permissions'
        elif perms == 'auth_or_read_only':
            perms_classes = 'IsAuthenticatedOrReadOnly'
            drf_import = ', permissions'
        elif perms == 'model':
            perms_classes = 'DjangoModelPermissionsWithRead'
            drg_import = 'from django_rest_generators import permissions\n'
        elif perms == 'model_or_read_only':
            perms_classes = 'DjangoModelPermissions'
            drf_import = ', permissions'
        elif perms == 'model_or_anon_read_only':
            perms_classes = 'DjangoModelPermissionsOrAnonReadOnly'
            drf_import = ', permissions'
        elif perms == 'object':
            perms_classes = 'DjangoObjectPermissionsWithRead'
            drg_import = 'from django_rest_generators import permissions\n'
        elif perms == 'object_or_read_only':
            perms_classes = 'DjangoObjectPermissions'
            drf_import = ', permissions'
        elif perms == 'object_or_anon_read_only':
            perms_classes = 'DjangoObjectPermissionsOrAnonReadOnly'
            drg_import = 'from django_rest_generators import permissions\n'
        else:
            perms_classes = 'IsAdminUser'
            drf_import = ', permissions'
        with open(viewset_file, "w+") as file:
            file.write("""%sfrom rest_framework import viewsets%s
from %s import models, serializers


class %s(viewsets.ModelViewSet):
    serializer_class = serializers.%s
    queryset = models.%s.objects.all()
    lookup_field = '%s'
    permission_classes = [
        permissions.%s
    ]
""" % (
                drg_import,
                drf_import,
                app,
                self.model_name,
                self.model_name,
                self.model_name,
                mapped['lookup_field'],
                perms_classes
            ))
        with open(viewset_init, "a+") as file:
            file.write("from .%s import %s\n" % (name, self.model_name))

    def _generate_routes(self, app, name):
        path = os.path.join(
            settings.BASE_DIR,
            app,
            "urls.py"
        )
        with open(path, "r+") as file:
            content = file.read()
            file.seek(0)
            file.truncate()
            content = content.replace('router = DefaultRouter()', '''router = DefaultRouter()
router.register(r'%s', viewsets.%s)''' % (name, self.model_name))
            file.write(content)

    def add_arguments(self, parser):
        parser.add_argument('app', help='Target application name')
        parser.add_argument('name', help='Target model name')
        parser.add_argument(
            '--permissions',
            '-p',
            default='everyone',
            help='Target permissions for the model',
            choices=[
                'everyone',
                'auth',
                'auth_or_read_only',
                'model',
                'model_or_read_only',
                'model_or_anon_read_only',
                'object',
                'object_or_read_only',
                'object_or_anon_read_only',
                'admin',
            ]
        )

    def _generate_permissions_tests(
            self,
            app,
            name,
            mapped,
            scenarios,
            givens,
            results_safe,
            results_unsafe
    ):
        path = os.path.join(
            settings.BASE_DIR,
            "features",
            "%s.%s.feature" % (app, name)
        )
        with open(path, "a+") as file:
            for i in range(0, len(scenarios)):
                file.write("""
Scenario: (Create) %s
Given a basic set of %s exists in the database
  And %s
When i prepare a request to /%s/1.0/%s/
    %s
    And i send the request using POST
Then the return code is %s
""" % (
                    scenarios[i],
                    name,
                    '\n  And '.join(givens[i]),
                    app,
                    name,
                    "\n      ".join([
                        "And i provide %s %s" % (
                            field,
                            mapped['test_generators'][field]('Create')
                        ) for field in mapped['fields']
                        if field not in self.read_only
                    ]),
                    "201" if results_unsafe[i] else "403"
                ))
                file.write("""
Scenario: (List) %s
Given a basic set of %s exists in the database
  And %s
When i prepare a request to /%s/1.0/%s/
  And i send the request using GET 
Then the return code is %s
""" % (
                    scenarios[i],
                    name,
                    '\n  And '.join(givens[i]),
                    app,
                    name,
                    "200" if results_safe[i] else "403"
                ))
                file.write("""
Scenario: (Get) %s
Given a basic set of %s exists in the database
  And %s
When i prepare a request to /%s/1.0/%s/%s/
  And i send the request using GET
Then the return code is %s
""" % (
                    scenarios[i],
                    name,
                    '\n  And '.join(givens[i]),
                    app,
                    name,
                    mapped['test_generators'][mapped['lookup_field']]('First'),
                    "200" if results_safe[i] else "403"
                ))
                file.write("""
Scenario: (Update) %s
Given a basic set of %s exists in the database
  And %s
When i prepare a request to /%s/1.0/%s/%s/
  %s
  And i send the request using PUT
Then the return code is %s
""" % (
                    scenarios[i],
                    name,
                    '\n  And '.join(givens[i]),
                    app,
                    name,
                    mapped['test_generators'][mapped['lookup_field']]('First'),
                    "\n      ".join([
                        "And i provide %s %s" % (
                            field,
                            mapped['test_generators'][field]('First')
                        ) for field in mapped['fields']
                        if field not in self.read_only
                    ]),
                    "200" if results_unsafe[i] else "403"
                ))
                file.write("""
Scenario: (Delete) %s
Given a basic set of %s exists in the database
  And %s
When i prepare a request to /%s/1.0/%s/%s/
  And i send the request using DELETE
Then the return code is %s
""" % (
                    scenarios[i],
                    name,
                    '\n  And '.join(givens[i]),
                    app,
                    name,
                    mapped['test_generators'][mapped['lookup_field']]('First'),
                    "204" if results_unsafe[i] else "403"
                ))

    @staticmethod
    def _generate_auth_tests():
        scenarios = [
            'Test logged permissions',
            'Test non-logged permissions'
        ]
        givens = [
            [
                'a basic set of users exists in the database',
                'i am logged in as unallowed_user'
            ],
            [
                'i am not logged in'
            ]
        ]
        results_safe = [
            True,
            False
        ]
        results_unsafe = [
            True,
            False
        ]
        return scenarios, givens, results_safe, results_unsafe

    @staticmethod
    def _generate_auth_or_tests():
        scenarios = [
            'Test logged permissions',
            'Test non-logged permissions'
        ]
        givens = [
            [
                'a basic set of users exists in the database',
                'i am logged in as unallowed_user'
            ],
            [
                'i am not logged in'
            ]
        ]
        results_safe = [
            True,
            True
        ]
        results_unsafe = [
            True,
            False
        ]
        return scenarios, givens, results_safe, results_unsafe

    @staticmethod
    def _generate_model_tests(app, name):
        scenarios = [
            'Test logged with rights permissions',
            'Test logged without rights permissions',
            'Test non-logged permissions'
        ]
        givens = [
            [
                'a basic set of users exists in the database',
                'i am logged in as allowed_user',
                'user allowed_user have permission %s.view_%s' % (app, name,),
                'user allowed_user have permission %s.add_%s' % (app, name,),
                'user allowed_user have permission %s.change_%s' % (app, name,),
                'user allowed_user have permission %s.delete_%s' % (app, name,)
            ],
            [
                'a basic set of users exists in the database',
                'i am logged in as unallowed_user'
            ],
            [
                'i am not logged in'
            ]
        ]
        results_safe = [
            True,
            False,
            False
        ]
        results_unsafe = [
            True,
            False,
            False
        ]
        return scenarios, givens, results_safe, results_unsafe

    @staticmethod
    def _generate_model_or_tests(app, name):
        scenarios = [
            'Test logged with rights permissions',
            'Test logged without rights permissions',
            'Test non-logged permissions'
        ]
        givens = [
            [
                'a basic set of users exists in the database',
                'i am logged in as allowed_user',
                'user allowed_user have permission %s.view_%s' % (app, name,),
                'user allowed_user have permission %s.add_%s' % (app, name,),
                'user allowed_user have permission %s.change_%s' % (app, name,),
                'user allowed_user have permission %s.delete_%s' % (app, name,)
            ],
            [
                'a basic set of users exists in the database',
                'i am logged in as unallowed_user'
            ],
            [
                'i am not logged in'
            ]
        ]
        results_safe = [
            True,
            True,
            False
        ]
        results_unsafe = [
            True,
            False,
            False
        ]
        return scenarios, givens, results_safe, results_unsafe

    @staticmethod
    def _generate_model_or_anon_tests(app, name):
        scenarios = [
            'Test logged with rights permissions',
            'Test logged without rights permissions',
            'Test non-logged permissions'
        ]
        givens = [
            [
                'a basic set of users exists in the database',
                'i am logged in as allowed_user',
                'user allowed_user have permission %s.view_%s' % (app, name,),
                'user allowed_user have permission %s.add_%s' % (app, name,),
                'user allowed_user have permission %s.change_%s' % (app, name,),
                'user allowed_user have permission %s.delete_%s' % (app, name,)
            ],
            [
                'a basic set of users exists in the database',
                'i am logged in as unallowed_user'
            ],
            [
                'i am not logged in'
            ]
        ]
        results_safe = [
            True,
            True,
            True
        ]
        results_unsafe = [
            True,
            False,
            False
        ]
        return scenarios, givens, results_safe, results_unsafe

    def _generate_object_tests(self, app, name, mapped):
        scenarios = [
            'Test logged with rights permissions',
            'Test logged without rights permissions',
            'Test non-logged permissions'
        ]
        givens = [
            [
                'a basic set of users exists in the database',
                'i am logged in as allowed_user',
                'user allowed_user have permission %s.view_%s' % (app, name,),
                'user allowed_user have permission %s.add_%s' % (app, name,),
                'user allowed_user have permission %s.change_%s' % (app, name,),
                'user allowed_user have permission %s.delete_%s' % (app, name,),
                'user allowed_user have permission %s.view_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                ),
                'user allowed_user have permission %s.add_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                ),
                'user allowed_user have permission %s.change_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                ),
                'user allowed_user have permission %s.delete_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                )
            ],
            [
                'a basic set of users exists in the database',
                'i am logged in as unallowed_user'
            ],
            [
                'i am not logged in'
            ]
        ]
        results_safe = [
            True,
            False,
            False
        ]
        results_unsafe = [
            True,
            False,
            False
        ]
        return scenarios, givens, results_safe, results_unsafe

    def _generate_object_or_tests(self, app, name, mapped):
        scenarios = [
            'Test logged with rights permissions',
            'Test logged without rights permissions',
            'Test non-logged permissions'
        ]
        givens = [
            [
                'a basic set of users exists in the database',
                'i am logged in as allowed_user',
                'user allowed_user have permission %s.view_%s' % (app, name,),
                'user allowed_user have permission %s.add_%s' % (app, name,),
                'user allowed_user have permission %s.change_%s' % (app, name,),
                'user allowed_user have permission %s.delete_%s' % (app, name,),
                'user allowed_user have permission %s.view_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                ),
                'user allowed_user have permission %s.add_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                ),
                'user allowed_user have permission %s.change_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                ),
                'user allowed_user have permission %s.delete_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                )
            ],
            [
                'a basic set of users exists in the database',
                'i am logged in as unallowed_user'
            ],
            [
                'i am not logged in'
            ]
        ]
        results_safe = [
            True,
            True,
            False
        ]
        results_unsafe = [
            True,
            False,
            False
        ]
        return scenarios, givens, results_safe, results_unsafe

    def _generate_object_or_anon_tests(self, app, name, mapped):
        scenarios = [
            'Test logged with rights permissions',
            'Test logged without rights permissions',
            'Test non-logged permissions'
        ]
        givens = [
            [
                'a basic set of users exists in the database',
                'i am logged in as allowed_user',
                'user allowed_user have permission %s.view_%s' % (app, name,),
                'user allowed_user have permission %s.add_%s' % (app, name,),
                'user allowed_user have permission %s.change_%s' % (app, name,),
                'user allowed_user have permission %s.delete_%s' % (app, name,),
                'user allowed_user have permission %s.view_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                ),
                'user allowed_user have permission %s.add_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                ),
                'user allowed_user have permission %s.change_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                ),
                'user allowed_user have permission %s.delete_%s over a %s.%s with %s %s' % (
                    app,
                    name,
                    app,
                    self.model_name,
                    mapped['lookup_field'],
                    mapped['test_generators'][mapped['lookup_field']]('First')
                )
            ],
            [
                'a basic set of users exists in the database',
                'i am logged in as unallowed_user'
            ],
            [
                'i am not logged in'
            ]
        ]
        results_safe = [
            True,
            True,
            True
        ]
        results_unsafe = [
            True,
            False,
            False
        ]
        return scenarios, givens, results_safe, results_unsafe

    @staticmethod
    def _generate_admin_tests():
        scenarios = [
            'Test logged as administrator',
            'Test logged as user',
            'Test non-logged permissions'
        ]
        givens = [
            [
                'a basic set of users exists in the database',
                'i am logged in as administrator',
            ],
            [
                'a basic set of users exists in the database',
                'i am logged in as unallowed_user'
            ],
            [
                'i am not logged in'
            ]
        ]
        results_safe = [
            True,
            False,
            False
        ]
        results_unsafe = [
            True,
            False,
            False
        ]
        return scenarios, givens, results_safe, results_unsafe

    def _generate_tests_for_permissions(self, app, name, mapped, perms):
        if perms == 'everyone':
            return
        elif perms == 'auth':
            (scenarios, givens, results_safe, results_unsafe) = Command._generate_auth_tests()
        elif perms == 'auth_or_read_only':
            (scenarios, givens, results_safe, results_unsafe) = Command._generate_auth_or_tests()
        elif perms == 'model':
            (scenarios, givens, results_safe, results_unsafe) = Command._generate_model_tests(app, name)
        elif perms == 'model_or_read_only':
            (scenarios, givens, results_safe, results_unsafe) = Command._generate_model_or_tests(app, name)
        elif perms == 'model_or_anon_read_only':
            (scenarios, givens, results_safe, results_unsafe) = Command._generate_model_or_anon_tests(app, name)
        elif perms == 'object':
            (scenarios, givens, results_safe, results_unsafe) = self._generate_object_tests(app, name, mapped)
        elif perms == 'object_or_read_only':
            (scenarios, givens, results_safe, results_unsafe) = self._generate_object_or_tests(app, name, mapped)
        elif perms == 'object_or_anon_read_only':
            (scenarios, givens, results_safe, results_unsafe) = self._generate_object_or_anon_tests(app, name, mapped)
        else:
            (scenarios, givens, results_safe, results_unsafe) = Command._generate_admin_tests()
        self._generate_permissions_tests(
            app,
            name,
            mapped,
            scenarios,
            givens,
            results_safe,
            results_unsafe
        )

    def handle(self, *args, **options):
        app = options['app']
        name = options['name']
        perms = options['permissions']
        self._import_model(app, name)
        mapped = self._map_properties()
        self._generate_serializer(app, name, mapped)
        self._generate_behavior_maker(app, name, mapped)
        self._generate_behavior_tests(app, name, mapped)
        self._generate_viewset(app, name, mapped, perms)
        self._generate_tests_for_permissions(app, name, mapped, perms)
        self._generate_routes(app, name)
