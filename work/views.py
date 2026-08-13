from asgiref.sync import sync_to_async
from rest_framework.views import APIView


class AsyncAPIView(APIView):
    async def dispatch(self, request, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request  # type: ignore
        self.headers = self.default_response_headers

        try:
            await sync_to_async(self.initial)(request, *args, **kwargs)
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
            response = await handler(request, *args, **kwargs)  # type: ignore
        except Exception as exc:  # noqa: BLE001
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response
