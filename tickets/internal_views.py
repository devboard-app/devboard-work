from rest_framework import status
from rest_framework.response import Response

from work.permissions import IsInternalService
from work.views import AsyncAPIView

from .repository import get_ticket_by_key


class InternalTicketByKeyView(AsyncAPIView):

    authentication_classes = []  # noqa: RUF012 internal service call, not a user request
    permission_classes = [IsInternalService]  # noqa: RUF012

    async def get(self, request, project_id, key):
        ticket = await get_ticket_by_key(project_id, key)
        if ticket is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response({"id": str(ticket.id), "project_id": project_id}, status=status.HTTP_200_OK)
