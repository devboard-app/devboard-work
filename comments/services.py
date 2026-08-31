from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from projects.models import ProjectMembership
from tickets.models import Ticket

from .models import Comment
from .repository import create_comment as create_comment_repository
from .repository import delete_comment as delete_comment_repository
from .repository import get_comment_by_id, get_comments_by_ticket
from .repository import update_comment as update_comment_repository


def _validate_body(body) -> str:
    if not isinstance(body, str) or not body.strip():
        raise ValidationError('Comment body is required.')
    return body.strip()

async def list_ticket_comments(ticket_id: str) -> list[Comment]:
    return await get_comments_by_ticket(ticket_id)

async def get_comment_or_404(comment_id: str, ticket_id: str) -> Comment:
    comment = await get_comment_by_id(comment_id, ticket_id)
    if comment is None:
        raise NotFound('Comment not found.')
    return comment

async def create_comment(ticket: Ticket, requester_id: str, data: dict) -> Comment:
    body = _validate_body(data.get('body'))
    return await create_comment_repository(ticket, requester_id, body)

async def update_comment(comment: Comment, requester_id: str, data: dict) -> Comment:
    if str(comment.author_id) != str(requester_id):
        raise PermissionDenied('You can only edit your own comments.')
    body = _validate_body(data.get('body'))
    if body == comment.body:
        return comment
    comment.body = body
    comment.is_edited = True
    return await update_comment_repository(comment)

async def delete_comment(comment: Comment, requester_id: str, requester_role: ProjectMembership.Role) -> None:
    if str(comment.author_id) != str(requester_id) and requester_role != ProjectMembership.Role.LEAD:
        raise PermissionDenied('You can only delete your own comments.')
    await delete_comment_repository(comment)