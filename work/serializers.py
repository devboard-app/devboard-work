from typing import Any, cast

from rest_framework.serializers import Serializer


def validated(serializer_class: type[Serializer], data: Any, *, partial: bool = False) -> dict:
    serializer = serializer_class(data=data, partial=partial)
    serializer.is_valid(raise_exception=True)
    return cast(dict, serializer.validated_data)