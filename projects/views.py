
from rest_framework import status
from rest_framework.response import Response

from teams.models import TeamMembership
from teams.permissions import require_team_role
from teams.services import get_team_or_404
from work.pagination import get_limit_offset, paginated
from work.serializers import validated
from work.views import AsyncAPIView

from .models import ProjectMembership
from .permissions import require_project_role
from .serializers import (
    ProjectInputSerializer,
    ProjectMemberInputSerializer,
    ProjectMemberRoleSerializer,
    ProjectMembershipSerializer,
    ProjectSerializer,
)
from .services import (
    add_project_member,
    create_project_with_lead,
    delete_project,
    get_project_member_or_404,
    get_project_or_404,
    list_project_members,
    list_team_projects,
    remove_project_member,
    update_project,
    update_project_member,
)

Role = TeamMembership.Role
class ProjectDetailView(AsyncAPIView):

    async def get(self, request, team_id, project_id):
        user_id = request.user.user_id
        await require_team_role(user_id, team_id, Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        project = await get_project_or_404(project_id, team_id)
        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def patch(self, request, team_id, project_id):
        user_id = request.user.user_id
        await require_team_role(user_id, team_id, Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        project = await get_project_or_404(project_id, team_id)
        await require_project_role(user_id, project_id, ProjectMembership.Role.LEAD)
        data = validated(ProjectInputSerializer, request.data, partial=True)
        updated_project= await update_project(project, data)
        serializer = ProjectSerializer(updated_project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def delete(self, request, team_id, project_id):
        user_id = request.user.user_id
        await require_team_role(user_id, team_id, Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        project = await get_project_or_404(project_id, team_id)
        await require_project_role(user_id, project_id, ProjectMembership.Role.LEAD)
        await delete_project(project)
        return Response(status=status.HTTP_204_NO_CONTENT)



class ProjectListCreateView(AsyncAPIView):

    async def get(self, request, team_id):
        await require_team_role(request.user.user_id, team_id, Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        limit, offset = get_limit_offset(request)
        projects, total = await list_team_projects(team_id, limit, offset)
        serializer = ProjectSerializer(projects, many=True)
        return Response(paginated(serializer.data, total, limit, offset), status=status.HTTP_200_OK)

    async def post(self, request, team_id):
        created_by = request.user.user_id
        await require_team_role(created_by, team_id, Role.OWNER, Role.ADMIN)
        data = validated(ProjectInputSerializer, request.data)
        team = await get_team_or_404(str(team_id))
        project = await create_project_with_lead(data, team, created_by)
        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProjectMemberView(AsyncAPIView):

    async def get(self, request, team_id, project_id):
        user_id = request.user.user_id
        await require_team_role(user_id, team_id, Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        await get_project_or_404(project_id, team_id)
        limit, offset = get_limit_offset(request)
        memberships, total = await list_project_members(project_id, limit, offset)
        serializer = ProjectMembershipSerializer(memberships, many=True)
        return Response(paginated(serializer.data, total, limit, offset), status=status.HTTP_200_OK)

    async def post(self, request, team_id, project_id):
        user_id = request.user.user_id
        await require_team_role(user_id, team_id, Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        project = await get_project_or_404(str(project_id), team_id)
        await require_project_role(user_id, str(project_id), ProjectMembership.Role.LEAD)
        data = validated(ProjectMemberInputSerializer, request.data)
        await require_team_role(data['user_id'], team_id, Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        membership = await add_project_member(project, data['user_id'], data['role'])
        serializer = ProjectMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    async def delete(self, request, team_id, project_id, user_id):
        requester_id = request.user.user_id
        await require_team_role(requester_id, team_id, Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        await get_project_or_404(str(project_id), team_id)
        await require_project_role(requester_id, str(project_id), ProjectMembership.Role.LEAD)
        await remove_project_member(str(project_id), str(user_id))
        return Response(status=status.HTTP_204_NO_CONTENT)

    async def patch(self, request, team_id, project_id, user_id):
        requester_id = request.user.user_id
        await require_team_role(requester_id, team_id, Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        await get_project_or_404(str(project_id), team_id)
        await require_project_role(requester_id, str(project_id), ProjectMembership.Role.LEAD)
        data = validated(ProjectMemberRoleSerializer, request.data)
        membership = await get_project_member_or_404(str(user_id), str(project_id))
        updated_membership = await update_project_member(membership, data['role'])
        serializer = ProjectMembershipSerializer(updated_membership)
        return Response(serializer.data, status=status.HTTP_200_OK)