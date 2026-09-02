from rest_framework import serializers

from work.serializers import validated

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

class PageQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(min_value=1, required=False, default=DEFAULT_LIMIT)
    offset = serializers.IntegerField(min_value=0, required=False, default=0)

def get_limit_offset(request) -> tuple [int, int]:
    data = validated(PageQuerySerializer, request.query_params)
    return min(data['limit'], MAX_LIMIT), data['offset']

def paginated(results, count: int, limit: int, offset: int) -> dict:
    return {'count': count, 'limit': limit, 'offset': offset, 'results': results}
