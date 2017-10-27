import json
from behave import use_step_matcher, when, then


use_step_matcher("re")


@when(r"i prepare a request to (?P<location>[a-zA-Z0-9\-_/.]+)")
def when_i_prepare_a_request(context, location):
    """
    :type location: str
    :type context: behave.runner.Context
    """
    context.apiRequestData = {
        'url': location,
        'params': {},
        'content-type': 'application/json',
        'format': 'json'
    }


@when(r"i provide (?P<key>[a-zA-Z0-9\-_]+) (?P<value>.+)")
def when_i_provide(context, key, value):
    """
    :type key: str
    :type value: str
    :type context: behave.runner.Context
    """
    context.apiRequestData['params'][key] = value


@when(r"i send the request using (?P<method>POST|GET|PUT|PATCH|DELETE)")
def when_i_send_the_request(context, method):
    """
    :type method: str
    :type context: behave.runner.Context
    """
    data = context.apiRequestData
    context.apiRequest = context.apiClient.generic(
        method,
        data['url'],
        data=json.dumps(data['params']),
        content_type=data['content-type'],
        format=data['format'],
    )


@then(r"the return code is (?P<code>[0-9]+)")
def then_the_return_code_is(context, code):
    """
    :type code: str
    :type context: behave.runner.Context
    """
    assert context.apiRequest.status_code == int(code)


@then(r"the return value for (?P<key>[a-zA-Z0-9\-_]+) is (?P<value>.+)")
def then_the_return_value_for_is(context, key, value):
    """
    :type key: str
    :type value: str
    :type context: behave.runner.Context
    """
    assert key in context.apiRequest.data
    assert str(context.apiRequest.data[key]) == str(value)


@then(r"the returned array contain (?P<cnt>[0-9]+) elements")
def then_the_returned_array_contain_elements(context, cnt):
    """
    :type cnt: str
    :type context: behave.runner.Context
    """
    assert len(context.apiRequest.data) == int(cnt)


@then(r"the returned element (?P<line>[0-9]+) have a"
      r" key named (?P<key>[a-zA-Z0-9_]+) with value (?P<value>.+)")
def then_then_returned_element_have_a_key(context, line, key, value):
    """
    :type line: str
    :type key: str
    :type value: str
    :type context: behave.runner.Context
    """
    line = int(line)
    data = context.apiRequest.data
    assert 0 <= line < len(data)
    row = data[line]
    assert key in row
    assert row[key] == value


@then(r"there is no (?P<key>[a-zA-Z0-9\-_]+) in the returned object")
def then_there_is_no(context, key):
    """
    :param context: behave.runner.Context
    :param key: str
    """
    assert key not in context.apiRequest.data


@then(
    r"the returned element (?P<line>[0-9]+) have no"
    r" key named (?P<key>[a-zA-Z0-9\-_]+)"
)
def then_the_return_element_have_no_key(context, line, key):
    """
    :param context: behave.runner.Context
    :param line: str
    :param key: str
    """
    line = int(line)
    data = context.apiRequest.data
    assert 0 <= line < len(data)
    assert key not in data[line]
