from behave import use_step_matcher, given, then
from django.apps import apps


use_step_matcher("re")


@then(r"a (?P<model_name>[a-zA-Z0-9_.]+) exists with (?P<key>[a-zA-Z0-9_]+) (?P<value>.+)")
def then_a_model_exists(context, model_name, key, value):
    """
    :type model_name: str
    :type key: str
    :type value: str
    :type context: behave.runner.Context
    """
    model = apps.get_model(model_name)
    args = {
        key: value
    }
    obj = model.objects.get(**args)
    assert obj is not None


@then(r"no (?P<model_name>[a-zA-Z0-9_.]+) exists with (?P<key>[a-zA-Z0-9_]+) (?P<value>.+)")
def then_no_model_exists(context, model_name, key, value):
    """
    :type model_name: str
    :type key: str
    :type value: str
    :type context: behave.runner.Context
    """
    model = apps.get_model(model_name)
    args = {
        key: value
    }
    obj = model.objects.filter(**args)
    assert len(obj) == 0
