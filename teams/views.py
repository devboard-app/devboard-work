import logging

import httpx
from rest_framework import status
from rest_framework.response import Response

from work.serializers import validated
from work.views import AsyncAPIView

from .infrastructure import send_member_notification
from .models import TeamMembership
from .permissions import require_team_role
from .repository import (
    get_membership_by_team,
)
from .serializers import (
    TeamInputSerializer,
    TeamMemberInputSerializer,
    TeamMemberRoleSerializer,
    TeamMembershipSerializer,
    TeamSerializer,
)
from .services import (
    add_member,
    change_member_role,
    create_team_with_owner,
    get_team_or_404,
    leave_team,
    list_my_teams,
    remove_member,
    update_team,
)

logger = logging.getLogger(__name__)
Role = TeamMembership.Role
class TeamListCreateView(AsyncAPIView):

    async def get(self, request):

        teams = await list_my_teams(request.user.user_id)
        serializer = TeamSerializer(teams, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request):

        data = validated(TeamInputSerializer, request.data)
        owner_id = request.user.user_id
        team = await create_team_with_owner(data['name'], data['description'], owner_id)
        serializer = TeamSerializer(team)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TeamDetailView(AsyncAPIView):

    async def get(self, request, pk):

        team = await get_team_or_404(str(pk))
        await require_team_role(request.user.user_id, str(pk), Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        serializer = TeamSerializer(team)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def patch(self, request, pk):

        team = await get_team_or_404(str(pk))
        await require_team_role(request.user.user_id, str(pk), Role.OWNER, Role.ADMIN)
        data = validated(TeamInputSerializer, request.data, partial=True)
        updated = await update_team(team, data)
        serializer = TeamSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def delete(self, request, pk):

        team = await get_team_or_404(str(pk))
        await require_team_role(request.user.user_id, str(pk), Role.OWNER)
        await team.adelete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TeamMemberListAddView(AsyncAPIView):

    async def get(self, request, pk):

        await get_team_or_404(str(pk))
        await require_team_role(request.user.user_id, str(pk), Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER)
        memberships = await get_membership_by_team(str(pk))
        serializer = TeamMembershipSerializer(memberships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, pk):

        team = await get_team_or_404(str(pk))
        requester_membership = await require_team_role(request.user.user_id, str(pk), Role.OWNER, Role.ADMIN)
        data = validated(TeamMemberInputSerializer, request.data)
        membership = await add_member(team, requester_membership.role, data['email'], data['role']) 
        try:
            await send_member_notification(data['email'], team.name, request.user.email)
        except (httpx.TransportError, httpx.HTTPStatusError) as e: 
            logger.error(f'Failed to send invitation email: {e}')
        serializer = TeamMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TeamMemberDetailView(AsyncAPIView):

    async def delete(self, request, pk, user_id):
        await get_team_or_404(str(pk))
        requester_membership = await require_team_role(request.user.user_id, str(pk), Role.OWNER, Role.ADMIN)
        await remove_member(str(pk), user_id, requester_membership.role)
        return Response(status=status.HTTP_204_NO_CONTENT)

    async def patch(self, request, pk, user_id):
        team = await get_team_or_404(str(pk))
        requester_membership = await require_team_role(request.user.user_id, str(pk), Role.OWNER, Role.ADMIN)
        requester_role = requester_membership.role
        data = validated(TeamMemberRoleSerializer, request.data)
        target_membership = await change_member_role(str(team.id), user_id, requester_role, data['role'])
        serializer = TeamMembershipSerializer(target_membership)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TeamMemberLeaveView(AsyncAPIView):

    async def delete(self, request, pk):
        await get_team_or_404(str(pk))
        await leave_team(str(pk), request.user.user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)