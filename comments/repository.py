from tickets.models import Ticket

from .models import Comment


async def get_comments_by_ticket(ticket_id: str, limit: int, offset: int) -> tuple[list[Comment], int]:
    qs = Comment.objects.filter(ticket_id=ticket_id)
    total = await qs.acount()
    return [c async for c in qs[offset:offset + limit]], total

async def get_comment_by_id(comment_id: str, ticket_id: str) -> Comment | None:
    return await Comment.objects.filter(id=comment_id, ticket_id=ticket_id).afirst()

async def create_comment(ticket: Ticket, author_id: str, body: str, attachment_ids: list, mentioned_user_ids: list) -> Comment:
    return await Comment.objects.acreate(ticket=ticket, author_id=author_id, body=body, attachment_ids=attachment_ids, mentioned_user_ids=mentioned_user_ids)

async def update_comment(comment: Comment) -> Comment:
    await comment.asave()
    return comment

async def delete_comment(comment: Comment) -> None:
    await comment.adelete()