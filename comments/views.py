from rest_framework import status
from rest_framework.response import Response

from projects.models import ProjectMembership
from projects.permissions import require_project_role
from teams.models import TeamMembership
from teams.permissions import require_team_role
from tickets.services import get_ticket_or_404
from work.views import AsyncAPIView

from .infrastructure import resolve_attachments
from .serializers import CommentSerializer
from .services import create_comment as create_comment_service
from .services import delete_comment as delete_comment_service
from .services import get_comment_or_404, list_ticket_comments
from .services import update_comment as update_comment_service

TeamRole = TeamMembership.Role
ProjectRole = ProjectMembership.Role


class CommentListCreateView(AsyncAPIView):

    async def get(self, request, team_id, project_id, ticket_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        await get_ticket_or_404(ticket_id, project_id)
        comments = await list_ticket_comments(ticket_id)
        ids = list(dict.fromkeys(str(i) for c in comments for i in c.attachment_ids))
        resolved = await resolve_attachments(ids)
        serializer = CommentSerializer(comments, many=True, context ={'resolved_attachments': resolved})
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def post(self, request, team_id, project_id, ticket_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        ticket = await get_ticket_or_404(ticket_id, project_id)
        comment = await create_comment_service(ticket, request.user.user_id, request.data)
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CommentDetailView(AsyncAPIView):
    async def patch(self, request, team_id, project_id, ticket_id, comment_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        ticket = await get_ticket_or_404(ticket_id, project_id)
        comment = await get_comment_or_404(comment_id, ticket_id)
        updated = await update_comment_service(comment, ticket, request.user.user_id, request.data)
        serializer = CommentSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    async def delete(self, request, team_id, project_id, ticket_id, comment_id):
        await require_team_role(request.user.user_id, team_id, TeamRole.OWNER, TeamRole.ADMIN, TeamRole.MEMBER, TeamRole.VIEWER)
        membership = await require_project_role(request.user.user_id, project_id, ProjectRole.LEAD, ProjectRole.CONTRIBUTOR)
        ticket = await get_ticket_or_404(ticket_id, project_id)
        comment = await get_comment_or_404(comment_id, ticket_id)
        await delete_comment_service(comment, ticket, request.user.user_id, ProjectMembership.Role(membership.role))
        return Response(status=status.HTTP_204_NO_CONTENT)