from typing import ClassVar

from asgiref.sync import sync_to_async
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from work.views import AsyncAPIView

from .models import TeamMembership
from .repository import (
    create_membership,
    create_team,
    get_team_by_id,
    get_teams_by_user,
)
from .serializers import TeamSerializer


class TeamListCreateView(AsyncAPIView):
    permission_classes: ClassVar = [IsAuthenticated]

    async def get(self, request):
        memberships = await get_teams_by_user(request.user.user_id)
        teams = [m.team for m in memberships]
        serializer = TeamSerializer(teams, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request):
        name = request.data.get('name')
        description = request.data.get('description')
        owner_id = request.user.get('user_id')
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
        serializer = TeamSerializer(team)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def patch(self, request, pk):
        team = await get_team_by_id(str(pk))
        if team is None:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TeamSerializer(team, data=request.data, partial=True)
        if await sync_to_async(serializer.is_valid)():
            await sync_to_async(serializer.save)()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    async def delete(self, request, pk):
        team = await get_team_by_id(str(pk))
        if team is None:
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)
        await sync_to_async(team.delete)()
        return Response(status=status.HTTP_204_NO_CONTENT)
    