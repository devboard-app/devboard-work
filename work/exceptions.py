from rest_framework.exceptions import APIException


class ServiceUnavailable(APIException):
    status_code = 502
    default_detail = 'A downstream service is unavailable.'
