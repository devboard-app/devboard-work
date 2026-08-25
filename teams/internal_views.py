from rest_framework import status
from rest_framework.response import Response

from teams.repository import get_membership_by_user_and_team
from work.permissions import IsInternalService
from work.views import AsyncAPIView


class InternalTeamCheckView(AsyncAPIView):
    
    authentication_classes = []  # noqa: RUF012 rewrite auth jwt check so it allows request from other microservice, not only an user
    permission_classes = [IsInternalService]  # noqa: RUF012

    async def get(self, request, user_id, team_id):
        membership = await get_membership_by_user_and_team(user_id, team_id)
        if membership is None:
            return Response('This member does not belong to the team.', status=status.HTTP_404_NOT_FOUND)
        return Response({"role": membership.role}, status=status.HTTP_200_OK)