from rest_framework.exceptions import APIException


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'A downstream service is unavailable.'

    
class Conflict(APIException):
    status_code = 409
    default_detail = 'This resource already exists.'
