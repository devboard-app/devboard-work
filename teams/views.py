from typing import ClassVar

from asgiref.sync import sync_to_async
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from work.views import AsyncAPIView

from .infrastructure import get_user_id_by_email
from .models import TeamMembership
from .permissions import can_assign_role, require_team_role
from .repository import (
    create_membership,
    create_team,
    delete_membership,
    get_membership_by_team,
    get_membership_by_user_and_team,
    get_team_by_id,
    get_teams_by_user,
)
from .serializers import TeamMembershipSerializer, TeamSerializer


class TeamListCreateView(AsyncAPIView):
    permission_classes: ClassVar = [IsAuthenticated]

    async def get(self, request):

        memberships = await get_teams_by_user(request.user.user_id)
        teams = [m.team for m in memberships]
        serializer = TeamSerializer(teams, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request):

        name = request.data.get('name')
        description = request.data.get('description', '')
        if not name:
            return Response({'detail': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)
        owner_id = request.user.user_id
        team =await create_team(name, description, owner_id)
        await create_membership(team, owner_id, TeamMembership.Role.OWNER)
        serializer = TeamSerializer(team)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TeamDetailView(AsyncAPIView):
    permission_classes: ClassVar = [IsAuthenticated]

    async def get(self, request, pk):

        team = await get_team_by_id(str(pk))
        if team is None:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        await require_team_role(request.user.user_id, str(pk), 'owner', 'admin', 'member', 'viewer')
        serializer = TeamSerializer(team)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def patch(self, request, pk):

        team = await get_team_by_id(str(pk))
        if team is None:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        await require_team_role(request.user.user_id, str(pk), 'owner', 'admin')
        serializer = TeamSerializer(team, data=request.data, partial=True)
        if await sync_to_async(serializer.is_valid)():
            await sync_to_async(serializer.save)()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    async def delete(self, request, pk):

        team = await get_team_by_id(str(pk))
        if team is None:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        await require_team_role(request.user.user_id, str(pk), 'owner')
        await sync_to_async(team.delete)()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TeamMemberListInviteView(AsyncAPIView):
    permission_classes: ClassVar = [IsAuthenticated]

    async def get(self, request, pk):

        team = await get_team_by_id(str(pk))
        if team is None:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        await require_team_role(request.user.user_id,  str(pk), 'owner', 'admin', 'member', 'viewer')
        memberships = await get_membership_by_team(str(pk))
        serializer = TeamMembershipSerializer(memberships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, pk):

        team = await get_team_by_id(str(pk))
        if team is None:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        requester_membership = await require_team_role(request.user.user_id, str(pk), 'owner', 'admin')
        target_role = request.data.get('role')
        if not can_assign_role(requester_membership.role, target_role):
            return Response({'detail': 'You cannot assign this role.'}, status=status.HTTP_403_FORBIDDEN)
        email = request.data.get('email')
        user_id = await get_user_id_by_email(email)
        if user_id is None:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        existing = await get_membership_by_user_and_team(str(user_id), str(pk))
        if existing is not None:
            return Response({'detail': 'User is already a member.'}, status=status.HTTP_409_CONFLICT)
        membership = await create_membership(team, user_id, target_role)
        serializer = TeamMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TeamMemberDetailView(AsyncAPIView):
    permission_classes: ClassVar = [IsAuthenticated]

    async def delete(self, request, pk, user_id):
        team = await get_team_by_id(str(pk))
        if team is None:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        await require_team_role(request.user.user_id, str(pk), 'owner', 'admin')

        target_membership = await get_membership_by_user_and_team(str(user_id),str(pk))
        if target_membership is None:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if target_membership.role == 'owner':
            return Response({'detail': 'Cannot remove a team owner.'}, status=status.HTTP_403_FORBIDDEN)
        await delete_membership(target_membership)
        return Response(status=status.HTTP_204_NO_CONTENT)

    async def patch(self, request, pk, user_id):
        team = await get_team_by_id(str(pk))
        if team is None:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        requester_membership = await require_team_role(request.user.user_id, str(pk), 'owner', 'admin')
        target_membership = await get_membership_by_user_and_team(str(user_id), str(pk))
        if target_membership is None:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        target_role = request.data.get('role')
        if not can_assign_role(requester_membership.role, target_role):
            return Response({'detail': 'You cannot assign this role.'}, status=status.HTTP_403_FORBIDDEN)
        target_membership.role = target_role
        await sync_to_async(target_membership.save)()
        serializer = TeamMembershipSerializer(target_membership)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TeamMemberLeaveView(AsyncAPIView):
    permission_classes: ClassVar = [IsAuthenticated]

    async def delete(self, request, pk):
        team = await get_team_by_id(str(pk))
        if team is None:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        membership = await get_membership_by_user_and_team(request.user.user_id, str(pk))
        if membership is None:
            return Response({'detail': 'You are not a member of this team.'}, status=status.HTTP_404_NOT_FOUND)
        if membership.role == 'owner':
            return Response({'detail': 'Cannot leave team if you are the owner.'}, status=status.HTTP_403_FORBIDDEN)
        await delete_membership(membership)
        return Response(status=status.HTTP_204_NO_CONTENT)