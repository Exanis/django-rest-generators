from distutils.core import setup

setup(
    name='Django rest tools',
    packages=['django_rest_tools'],
    version='0.1',
    description='Simple tool to add a bunch of commands related to django_rest_framework, django_guardian and behave',
    author='Yann Piquet',
    author_email='yann.piquet@epitech.eu',
    install_requires=[
        'djangorestframework',
        'django-guardian',
        'behave'
    ],
    license='MIT',
    url='https://github.com/Exanis/django-rest-tools',
    download_url='https://github.com/Exanis/django-rest-tools/archive/0.1.tar.gz',
    keywords=['testing', 'django', 'djangorestframework', 'behave'],
    classifiers=[],
    include_package_data=True
)
