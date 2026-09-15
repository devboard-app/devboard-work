from rest_framework import status
from rest_framework.response import Response

from projects.repository import get_project_by_id, get_project_membership
from work.permissions import IsInternalService
from work.views import AsyncAPIView


class InternalProjectCheckView(AsyncAPIView):
    
    authentication_classes = []  # noqa: RUF012 rewrite auth jwt check so it allows request from other microservice, not only an user
    permission_classes = [IsInternalService]  # noqa: RUF012

    async def get(self, request, user_id, project_id):
        membership = await get_project_membership(user_id, project_id)
        if membership is None:
            return Response('This member does not belong to the project.', status=status.HTTP_404_NOT_FOUND)
        return Response({"role": membership.role}, status=status.HTTP_200_OK)

class InternalProjectTeamCheckView(AsyncAPIView):
    authentication_classes = []  # noqa: RUF012 internal service-to-service call, no user JWT
    permission_classes = [IsInternalService]  # noqa: RUF012

    async def get(self, request, team_id, project_id):
        project = await get_project_by_id(project_id, team_id)
        if project is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_200_OK)
