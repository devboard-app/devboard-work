from django.db.models import Max

from projects.models import Project

from .models import Ticket


async def get_ticket_by_id(ticket_id: str, project_id: str) -> Ticket | None:
    return await Ticket.objects.filter(id=ticket_id, project_id=project_id).prefetch_related('labels').afirst()

async def get_tickets_by_project(project_id: str) -> list[Ticket]:
    return [m async for m in Ticket.objects.filter(project=project_id).prefetch_related('labels')]

async def get_next_ticket_number(project_id: str) -> int:
    result = await Ticket.objects.filter(project=project_id).aaggregate(max_number=Max('ticket_number'))
    return (result['max_number'] or 0) +1

async def create_ticket(
        title: str,
        description: str,
        type: Ticket.Type,
        priority: Ticket.Priority,
        status: Ticket.Status,
        project: Project,
        created_by: str,
        ticket_number: int,
        key: str,
        assignee_id: str | None = None,
        parent_epic: Ticket | None = None,
        due_date = None,
        story_points: int | None = None) -> Ticket:
    return await Ticket.objects.acreate(
        title=title, 
        description=description,
        type=type,
        priority=priority,
        status=status,
        project=project,
        created_by=created_by,
        ticket_number=ticket_number,
        key=key,
        assignee_id=assignee_id,
        parent_epic=parent_epic,
        due_date=due_date,
        story_points=story_points,
    )

async def update_ticket(ticket: Ticket) -> Ticket:
    await ticket.asave()
    return ticket

async def delete_ticket(ticket: Ticket) -> None:
    await ticket.adelete()

async def get_tickets_by_project_and_no_sprint(project_id: str) -> list[Ticket]:
    return [t async for t in Ticket.objects.filter(project=project_id, sprint__isnull=True).prefetch_related('labels')]

async def get_ticket_by_key(project_id: str, key: str) -> Ticket | None:
    return await Ticket.objects.filter(project_id=project_id, key=key).afirst()