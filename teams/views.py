
from asgiref.sync import sync_to_async
from rest_framework import status
from rest_framework.response import Response

from work.views import AsyncAPIView

from .infrastructure import send_invitation_email
from .permissions import require_team_role
from .repository import (
    get_membership_by_team,
)
from .serializers import TeamMembershipSerializer, TeamSerializer
from .services import (
    change_member_role,
    create_team_with_owner,
    get_team_or_404,
    invite_member,
    leave_team,
    list_my_teams,
    remove_member,
)


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
        await require_team_role(request.user.user_id, str(pk), 'owner', 'admin', 'member', 'viewer')
        serializer = TeamSerializer(team)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def patch(self, request, pk):

        team = await get_team_or_404(str(pk))
        await require_team_role(request.user.user_id, str(pk), 'owner', 'admin')
        serializer = TeamSerializer(team, data=request.data, partial=True)
        if await sync_to_async(serializer.is_valid)():
            await sync_to_async(serializer.save)()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    async def delete(self, request, pk):

        team = await get_team_or_404(str(pk))
        await require_team_role(request.user.user_id, str(pk), 'owner')
        await team.adelete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TeamMemberListInviteView(AsyncAPIView):

    async def get(self, request, pk):

        await get_team_or_404(str(pk))
        await require_team_role(request.user.user_id, str(pk), 'owner', 'admin', 'member', 'viewer')
        memberships = await get_membership_by_team(str(pk))
        serializer = TeamMembershipSerializer(memberships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, pk):

        team = await get_team_or_404(str(pk))
        requester_membership = await require_team_role(request.user.user_id, str(pk), 'owner', 'admin')
        target_role = request.data.get('role')
        target_email = request.data.get('email')
        membership = await invite_member(team, requester_membership.role, target_email, target_role) 
        await send_invitation_email(target_email, team.name, request.user.email)
        serializer = TeamMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TeamMemberDetailView(AsyncAPIView):

    async def delete(self, request, pk, user_id):
        await get_team_or_404(str(pk))
        requester_membership = await require_team_role(request.user.user_id, str(pk), 'owner', 'admin')
        await remove_member(str(pk), user_id, requester_membership.role)
        return Response(status=status.HTTP_204_NO_CONTENT)

    async def patch(self, request, pk, user_id):
        team = await get_team_or_404(str(pk))
        requester_membership = await require_team_role(request.user.user_id, str(pk), 'owner', 'admin')
        requester_role = requester_membership.role
        target_role = request.data.get('role')
        target_membership = await change_member_role(str(team.id), user_id, requester_role, target_role)
        serializer = TeamMembershipSerializer(target_membership)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TeamMemberLeaveView(AsyncAPIView):

    async def delete(self, request, pk):
        await get_team_or_404(str(pk))
        await leave_team(str(pk), request.user.user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)