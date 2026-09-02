import uuid

from rest_framework.exceptions import NotFound, PermissionDenied

from projects.models import ProjectMembership
from projects.repository import get_memberships_by_project
from tickets.models import Ticket
from work.infrastructure.events import (
    publish_comment_created,
    publish_comment_deleted,
    publish_comment_mentioned,
    publish_comment_updated,
)

from .infrastructure import resolve_usernames
from .mentions import extract_mentions
from .models import Comment
from .repository import create_comment as create_comment_repository
from .repository import delete_comment as delete_comment_repository
from .repository import get_comment_by_id, get_comments_by_ticket
from .repository import update_comment as update_comment_repository


async def _resolve_mentions(body: str, author_id: str, project_id: str) -> list[uuid.UUID]:
    usernames = extract_mentions(body)
    if not usernames:
        return []

    resolved = await resolve_usernames(usernames)
    if not resolved:
        return[]

    member_ids ={str(m.user_id) for m in await get_memberships_by_project(project_id)}

    mentioned = []
    for username in usernames:
        user_id = resolved.get(username)
        if user_id is None:
            continue
        if str(user_id) == str(author_id):
            continue
        if str(user_id) not in member_ids:
            continue
        mentioned.append(uuid.UUID(str(user_id)))
    return mentioned

async def list_ticket_comments(ticket_id: str) -> list[Comment]:
    return await get_comments_by_ticket(ticket_id)

async def get_comment_or_404(comment_id: str, ticket_id: str) -> Comment:
    comment = await get_comment_by_id(comment_id, ticket_id)
    if comment is None:
        raise NotFound('Comment not found.')
    return comment

async def create_comment(ticket: Ticket, requester_id: str, data: dict) -> Comment:
    body = data['body']
    attachment_ids = data['attachment_ids']
    mentioned_user_ids = await _resolve_mentions(body, requester_id, ticket.project_id)  # type: ignore
    comment = await create_comment_repository(ticket, requester_id, body, attachment_ids, mentioned_user_ids)
    # notify the assignee only if they were not mentioned
    notified = {uuid.UUID(requester_id), *mentioned_user_ids}
    assignee_id = ticket.assignee_id if ticket.assignee_id not in notified else None
    await publish_comment_created(comment, ticket, actor_id=requester_id, recipient_id=assignee_id)
    for recipient_id in comment.mentioned_user_ids:
        await publish_comment_mentioned(comment, ticket, actor_id=requester_id, recipient_id=str(recipient_id))
    return comment

async def update_comment(comment: Comment, ticket: Ticket, requester_id: str, data: dict) -> Comment:
    if str(comment.author_id) != str(requester_id):
        raise PermissionDenied('You can only edit your own comments.')
    body = data['body']
    if body == comment.body:
        return comment
    
    previously_mentioned = {str(i) for i in comment.mentioned_user_ids}

    comment.body = body
    comment.mentioned_user_ids = await _resolve_mentions(body, requester_id, ticket.project_id) #type: ignore
    comment.is_edited = True
    updated = await update_comment_repository(comment)

    await publish_comment_updated(updated, ticket, actor_id=requester_id)
    for recipient_id in updated.mentioned_user_ids:
        if str(recipient_id) not in previously_mentioned:
            await publish_comment_mentioned(updated, ticket, actor_id=requester_id, recipient_id=str(recipient_id))
    return updated

async def delete_comment(comment: Comment, ticket: Ticket, requester_id: str, requester_role: ProjectMembership.Role) -> None:
    if str(comment.author_id) != str(requester_id) and requester_role != ProjectMembership.Role.LEAD:
        raise PermissionDenied('You can only delete your own comments.')
    comment_id = comment.id
    await delete_comment_repository(comment)
    await publish_comment_deleted(ticket.project_id, comment_id, ticket.id, ticket.key, actor_id=requester_id) #type: ignore