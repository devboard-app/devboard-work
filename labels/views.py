
from rest_framework import status
from rest_framework.response import Response

from projects.models import ProjectMembership
from projects.services import get_project_or_404
from teams.models import TeamMembership
from tickets.services import get_ticket_or_404
from work.views import AsyncAPIView

from .permissions import require_project_role, require_team_role
from .serializers import LabelListSerializer, LabelSerializer
from .services import (
    apply_label_to_ticket,
    create_label,
    delete_label,
    get_label_or_404,
    get_ticket_labels,
    list_project_labels,
    remove_label_from_ticket,
    update_label,
)

TeamRole = TeamMembership.Role
ProjectRole = ProjectMembership.Role

class LabelListCreateView(AsyncAPIView):

    async def get(self, request, team_id, project_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        labels = await list_project_labels(project_id)
        serializer = LabelListSerializer(labels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, team_id, project_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        label = await create_label(await get_project_or_404(project_id, team_id) , request.data)
        serializer = LabelSerializer(label)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LabelDetailView(AsyncAPIView):

    async def get(self, request, team_id, project_id, label_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        label = await get_label_or_404(label_id)
        serializer = LabelSerializer(label)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def patch(self, request, team_id, project_id, label_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        label = await get_label_or_404(label_id)
        updated_label = await update_label(label, request.data)
        serializer = LabelSerializer(updated_label)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def delete(self, request, team_id, project_id, label_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD)
        label = await get_label_or_404(label_id)
        await delete_label(label)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class TicketLabelView(AsyncAPIView):

    async def get(self, request, team_id, project_id, ticket_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        ticket = await get_ticket_or_404(ticket_id)
        labels = await get_ticket_labels(ticket)
        serializer = LabelListSerializer(labels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, team_id, project_id, ticket_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        membership = await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        ticket = await get_ticket_or_404(ticket_id)
        label = await get_label_or_404(request.data.get('label_id'))
        await apply_label_to_ticket(ticket, label, request.user.user_id, ProjectMembership.Role(membership.role))
        return Response(status=status.HTTP_200_OK)

    async def delete(self, request, team_id, project_id, ticket_id, label_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        membership = await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        ticket = await get_ticket_or_404(ticket_id)
        label = await get_label_or_404(label_id)
        await remove_label_from_ticket(ticket, label, request.user.user_id, ProjectMembership.Role(membership.role))
        return Response(status=status.HTTP_204_NO_CONTENT)

    