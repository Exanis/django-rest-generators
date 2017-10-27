from behave import use_step_matcher, given
from django.apps import apps
from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm


use_step_matcher("re")


@given(r"i am logged in as (?P<username>[^ ]+)")
def given_i_am_logged_in(context, username):
    """
    :type username: str
    :type context: behave.runner.Context
    """
    user = get_user_model().objects.get(username=username)
    context.apiClient.force_authenticate(user=user)


@given(r"i am not logged in")
def given_i_am_not_logged_in(context):
    """
    :type context: behave.runner.Context
    """
    pass


@given(r"a basic set of users exists in the database")
def basic_set_of_users_exists_in_the_database(context):
    """
    :type context: behave.runner.Context
    """
    user_model = get_user_model()
    user_model.objects.create(
        username='administrator',
        is_staff=True
    )
    user_model.objects.create(
        username='allowed_user'
    )
    user_model.objects.create(
        username='unallowed_user'
    )


@given(r'a super administrator exists in the database')
def a_super_administrator_exists_in_the_database(context):
    user_model = get_user_model()
    user_model.objects.create(
        username='superadmin',
        is_staff=True,
        is_superuser=True
    )


@given(r"user (?P<user>[^ ]+) have permission (?P<perm>[^ ]+)")
def user_have_permission(context, user, perm):
    user = get_user_model().objects.get(username=user)
    assign_perm(perm, user)


@given(r"user (?P<user>[^ ]+) have permission (?P<perm>[^ ]+) over a (?P<model>[^ ]+) with (?P<key>[^ ]+) (?P<key_value>.+)")
def user_have_permission_over_a_with(context, user, perm, model, key, key_value):
    user = get_user_model().objects.get(username=user)
    obj_model = apps.get_model(model)
    args = {
        key: key_value
    }
    obj = obj_model.objects.get(**args)
    assign_perm(perm, user, obj)
