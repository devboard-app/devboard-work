
from rest_framework import status
from rest_framework.response import Response

from teams.permissions import require_team_role
from teams.services import get_team_or_404
from work.views import AsyncAPIView

from .permissions import require_project_role
from .repository import get_projects_by_team
from .serializers import ProjectSerializer
from .services import (
    create_project_with_lead,
    delete_project,
    get_project_or_404,
    update_project,
)


class ProjectDetailView(AsyncAPIView):

    async def get(self, request, team_id, project_id):
        user_id = request.user.user_id
        await require_team_role(user_id, team_id, 'owner', 'admin', 'member', 'viewer')
        project = await get_project_or_404(project_id)
        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def patch(self, request, team_id, project_id):
        user_id = request.user.user_id
        await require_team_role(user_id, team_id, 'owner', 'admin', 'member', 'viewer')
        project = await get_project_or_404(project_id)
        await require_project_role(user_id, project_id, 'lead')
        updated_project= await update_project(project, request.data)
        serializer = ProjectSerializer(updated_project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def delete(self, request, team_id, project_id):
        user_id = request.user.user_id
        await require_team_role(user_id, team_id, 'owner', 'admin', 'member', 'viewer')
        project = await get_project_or_404(project_id)
        await require_project_role(user_id, project_id, 'lead')
        await delete_project(project)
        return Response(status=status.HTTP_204_NO_CONTENT)



class ProjectListCreateView(AsyncAPIView):

    async def get(self, request, team_id):
        await require_team_role(request.user.user_id, team_id, 'owner','admin','member','viewer')
        projects = await get_projects_by_team(team_id)
        serializer = ProjectSerializer(projects, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, team_id):
        created_by = request.user.user_id
        await require_team_role(created_by, team_id, 'owner', 'admin')
        name = request.data.get('name')
        key = request.data.get('key')
        description = request.data.get('description', '')
        if not name or not key: 
            return Response({'detail': 'Name and key fields are required.'}, status=status.HTTP_400_BAD_REQUEST)
        team = await get_team_or_404(str(team_id))
        project = await create_project_with_lead(name, key, description, team, created_by)
        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
