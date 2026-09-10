import uuid

from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from outbox.writer import awrite_with_outbox
from projects.models import ProjectMembership
from projects.repository import get_memberships_by_project
from tickets.models import Ticket
from work.infrastructure.events import build_payload

from .infrastructure import resolve_usernames, verify_attachments
from .mentions import extract_mentions
from .models import Comment
from .repository import (
    create_comment_sync,
    delete_comment_sync,
    get_comment_by_id,
    get_comments_by_ticket,
    update_comment_sync,
)


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

async def list_ticket_comments(ticket_id: str, limit: int, offset: int) -> tuple[list[Comment], int]:
    return await get_comments_by_ticket(ticket_id, limit, offset)

async def get_comment_or_404(comment_id: str, ticket_id: str) -> Comment:
    comment = await get_comment_by_id(comment_id, ticket_id)
    if comment is None:
        raise NotFound('Comment not found.')
    return comment

async def create_comment(ticket: Ticket, requester_id: str, data: dict) -> Comment:
    body = data['body']
    attachment_ids = data['attachment_ids']
    if attachment_ids:
        requested = {str(i) for i in attachment_ids}
        if await verify_attachments(sorted(requested), requester_id) != requested:
            raise ValidationError({'attachment_ids': "Unknown attachment, or it does not belong to you."})
    mentioned_user_ids = await _resolve_mentions(body, requester_id, ticket.project_id)  # type: ignore
    comment_id = uuid.uuid4()

    # notify the assignee only if they were not mentioned
    notified = {uuid.UUID(requester_id), *mentioned_user_ids}
    assignee_id = ticket.assignee_id if ticket.assignee_id not in notified else None

    events = [('redis_stream', build_payload('comment.created', project_id=ticket.project_id, actor_id=requester_id, recipient_id=assignee_id, comment_id=comment_id, ticket_id=ticket.id, ticket_key=ticket.key))] # type: ignore
    for recipient_id in mentioned_user_ids:
        events.append(('redis_stream', build_payload('comment.mentioned', project_id=ticket.project_id, actor_id=requester_id, recipient_id=str(recipient_id), comment_id=comment_id, ticket_id=ticket.id, ticket_key=ticket.key))) # type: ignore
    def _create():
        return create_comment_sync(comment_id, ticket, requester_id, body, attachment_ids, mentioned_user_ids)

    return await awrite_with_outbox(_create, events)

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

    events = [('redis_stream', build_payload('comment.updated', project_id=ticket.project_id, actor_id=requester_id, comment_id=comment.id, ticket_id=ticket.id, ticket_key=ticket.key))] # type: ignore
    for recipient_id in comment.mentioned_user_ids:
        if str(recipient_id) not in previously_mentioned:
            events.append(('redis_stream', build_payload('comment.mentioned', project_id=ticket.project_id, actor_id=requester_id, recipient_id=str(recipient_id), comment_id=comment.id, ticket_id=ticket.id, ticket_key=ticket.key))) # type: ignore

    def _save():
        return update_comment_sync(comment)

    return await awrite_with_outbox(_save, events)

async def delete_comment(comment: Comment, ticket: Ticket, requester_id: str, requester_role: ProjectMembership.Role) -> None:
    if str(comment.author_id) != str(requester_id) and requester_role != ProjectMembership.Role.LEAD:
        raise PermissionDenied('You can only delete your own comments.')
    comment_id = comment.id
    payload = build_payload('comment.deleted', project_id=ticket.project_id, actor_id=requester_id, comment_id=comment_id, ticket_id=ticket.id, ticket_key=ticket.key) # type: ignore
    def _delete():
        return delete_comment_sync(comment)
    await awrite_with_outbox(_delete, [('redis_stream', payload)])