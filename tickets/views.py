from rest_framework import status
from rest_framework.response import Response

from projects.models import ProjectMembership
from projects.services import get_project_or_404
from sprints.serializers import SprintListSerializer
from teams.models import TeamMembership
from work.pagination import get_limit_offset, paginated
from work.serializers import validated
from work.views import AsyncAPIView

from .permissions import require_project_role, require_team_role
from .serializers import TicketInputSerializer, TicketListSerializer, TicketSerializer
from .services import (
    create_ticket,
    delete_ticket,
    get_backlog,
    get_board,
    get_ticket_or_404,
    list_project_tickets,
    update_ticket,
)

TeamRole = TeamMembership.Role
ProjectRole = ProjectMembership.Role
class TicketListCreateView(AsyncAPIView):

    async def get(self, request, team_id, project_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        limit, offset = get_limit_offset(request)
        tickets, total = await list_project_tickets(project_id, limit, offset)
        serializer = TicketListSerializer(tickets, many=True)
        return Response(paginated(serializer.data, total, limit, offset), status=status.HTTP_200_OK)

    async def post(self, request, team_id, project_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        membership = await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        data = validated(TicketInputSerializer, request.data)
        ticket = await create_ticket(await get_project_or_404(project_id, team_id), request.user.user_id, ProjectMembership.Role(membership.role), data)
        ticket = await get_ticket_or_404(str(ticket.id), project_id)
        serializer = TicketSerializer(ticket)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TicketDetailView(AsyncAPIView):

    async def get(self, request, team_id, project_id, ticket_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        ticket = await get_ticket_or_404(ticket_id, project_id)
        serializer = TicketSerializer(ticket)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def patch(self, request, team_id, project_id, ticket_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        membership = await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        ticket = await get_ticket_or_404(ticket_id, project_id)
        data = validated(TicketInputSerializer, request.data, partial=True)
        updated_ticket = await update_ticket(ticket, request.user.user_id, ProjectMembership.Role(membership.role), data)
        serializer = TicketSerializer(updated_ticket)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def delete(self, request, team_id, project_id, ticket_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        ticket = await get_ticket_or_404(ticket_id, project_id)
        await delete_ticket(ticket, request.user.user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

class BoardView(AsyncAPIView):

    async def get(self, request, team_id, project_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        result = await get_board(str(project_id))
        if result['sprint'] is None:
            return Response(result, status=status.HTTP_200_OK)
        serialized_sprint = SprintListSerializer(result['sprint']).data
        serialized_board = {}
        for column, tickets in result['board'].items():
            serialized_board[column] = TicketSerializer(tickets, many=True).data

        return Response({
            'sprint': serialized_sprint,
            'board': serialized_board,
        }, status=status.HTTP_200_OK)

class BacklogView(AsyncAPIView):

    async def get(self, request, team_id, project_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        limit, offset =  get_limit_offset(request)
        tickets, total = await get_backlog(str(project_id), limit, offset)
        serializer = TicketSerializer(tickets, many=True)
        return Response(paginated(serializer.data, total, limit, offset), status=status.HTTP_200_OK)