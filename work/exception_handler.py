from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    data = response.data

    if isinstance(data, dict) and list(data.keys()) == ['detail']:
        response.data = {'detail': str(data['detail']), 'errors': None}
        return response

    if isinstance(data, dict):
        errors = {
            field: [str(v) for v in value] if isinstance(value, list) else [str(value)]
            for field, value in data.items()
        }
    else:
        items = data if isinstance(data, list) else [data]
        errors = {'non_field_errors': [str(item) for item in items]}

    response.data = {'detail': next(iter(errors.values()))[0], 'errors': errors}
    return response