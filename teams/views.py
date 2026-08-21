import logging

import httpx
from asgiref.sync import sync_to_async
from rest_framework import status
from rest_framework.response import Response

from work.views import AsyncAPIView

from .infrastructure import send_member_notification
from .models import TeamMembership
from .permissions import require_team_role
from .repository import (
    get_membership_by_team,
)
from .serializers import TeamMembershipSerializer, TeamSerializer
from .services import (
    add_member,
    change_member_role,
    create_team_with_owner,
    get_team_or_404,
    leave_team,
    list_my_teams,
    remove_member,
)

logger = logging.getLogger(__name__)
Role = TeamMembership.Role
class TeamListCreateView(AsyncAPIView):

    async def get(self, request):

        teams = await list_my_teams(request.user.user_id)
        serializer = TeamSerializer(teams, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request):

        name = request.data.get('name')
        description = request.data.get('description', '')
        if not name:
            return Response({'detail': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)
        owner_id = request.user.user_id

        team = await create_team_with_owner(name, description, owner_id)

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
        serializer = TeamSerializer(team, data=request.data, partial=True)
        if await sync_to_async(serializer.is_valid)():
            await sync_to_async(serializer.save)()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        target_role = request.data.get('role')
        target_email = request.data.get('email')
        if not target_role or not target_email:
            return Response({'detail':'Email and role are required.'}, status=status.HTTP_400_BAD_REQUEST)
        membership = await add_member(team, requester_membership.role, target_email, target_role) 
        try:
            await send_member_notification(target_email, team.name, request.user.email)
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
        target_role = request.data.get('role')
        if not target_role:
            return Response({'detail':'Role is required.'}, status=status.HTTP_400_BAD_REQUEST)

        target_membership = await change_member_role(str(team.id), user_id, requester_role, target_role)
        serializer = TeamMembershipSerializer(target_membership)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TeamMemberLeaveView(AsyncAPIView):

    async def delete(self, request, pk):
        await get_team_or_404(str(pk))
        await leave_team(str(pk), request.user.user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)