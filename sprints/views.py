from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from projects.models import ProjectMembership
from projects.services import get_project_or_404
from teams.models import TeamMembership
from tickets.serializers import TicketSerializer
from tickets.services import get_ticket_or_404
from work.serializers import validated
from work.views import AsyncAPIView

from .permissions import require_project_role, require_team_role
from .serializers import (
    SprintInputSerializer,
    SprintListSerializer,
    SprintSerializer,
    SprintTicketInputSerializer,
)
from .services import (
    add_ticket_to_sprint,
    complete_sprint,
    create_sprint,
    delete_sprint,
    get_sprint_or_404,
    list_project_sprints,
    list_sprint_tickets,
    remove_ticket_from_sprint,
    start_sprint,
    update_sprint,
)

TeamRole = TeamMembership.Role
ProjectRole = ProjectMembership.Role

class SprintListCreateView(AsyncAPIView):

    async def get(self, request, team_id, project_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        sprints = await list_project_sprints(project_id)
        serializer = SprintListSerializer(sprints, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, team_id, project_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        project = await get_project_or_404(project_id, team_id)
        data = validated(SprintInputSerializer, request.data)
        sprint = await create_sprint(project, request.user.user_id, data)
        serializer = SprintSerializer(sprint)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class SprintDetailView(AsyncAPIView):

    async def get(self, request, team_id, project_id, sprint_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        sprint = await get_sprint_or_404(sprint_id, project_id)
        serializer = SprintSerializer(sprint)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def patch(self, request, team_id, project_id, sprint_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        sprint = await get_sprint_or_404(sprint_id, project_id)
        data = validated(SprintInputSerializer, request.data, partial=True)
        updated_sprint = await update_sprint(sprint, data)
        serializer = SprintSerializer(updated_sprint)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def delete(self, request, team_id, project_id, sprint_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        sprint = await get_sprint_or_404(sprint_id, project_id)
        await delete_sprint(sprint)
        return Response(status=status.HTTP_204_NO_CONTENT)

class SprintStartView(AsyncAPIView):

    async def post(self, request, team_id, project_id, sprint_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        sprint = await get_sprint_or_404(sprint_id, project_id)
        started_sprint = await start_sprint(sprint, project_id, team_id, request.user.user_id)
        serializer = SprintSerializer(started_sprint)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SprintCompleteView(AsyncAPIView):

    async def post(self, request, team_id, project_id, sprint_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        sprint = await get_sprint_or_404(sprint_id, project_id)
        completed_sprint = await complete_sprint(sprint, team_id, request.user.user_id)
        serializer = SprintSerializer(completed_sprint)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SprintTicketView(AsyncAPIView):

    async def get(self, request, team_id, project_id, sprint_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        sprint = await get_sprint_or_404(sprint_id, project_id)
        tickets = await list_sprint_tickets(sprint)
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, team_id, project_id, sprint_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        sprint = await get_sprint_or_404(sprint_id, project_id)
        data = validated(SprintTicketInputSerializer, request.data)
        ticket = await get_ticket_or_404(str(data['ticket_id']), project_id)
        await add_ticket_to_sprint(sprint, ticket, request.user.user_id)
        return Response(status=status.HTTP_200_OK)

    async def delete(self, request, team_id, project_id, sprint_id, ticket_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        sprint = await get_sprint_or_404(sprint_id, project_id)
        ticket = await get_ticket_or_404(ticket_id, project_id)
        if ticket.sprint_id != sprint.id: #type: ignore
            raise ValidationError('Ticket does not belong to this sprint.')
        await remove_ticket_from_sprint(ticket, sprint, request.user.user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)