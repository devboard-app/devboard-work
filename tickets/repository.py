from projects.models import Project

from .models import Ticket


async def get_ticket_by_id(ticket_id: str) -> Ticket | None:
    return await Ticket.objects.filter(id=ticket_id).prefetch_related('labels').afirst()

async def get_tickets_by_project(project_id: str) -> list[Ticket]:
    return [m async for m in Ticket.objects.filter(project=project_id).prefetch_related('labels')]

async def get_next_ticket_number(project_id: str) -> int:
    return await Ticket.objects.filter(project=project_id).acount() + 1

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
        due_date = None) -> Ticket:
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
        due_date=due_date
    )

async def update_ticket(ticket: Ticket) -> Ticket:
    await ticket.asave()
    return ticket

async def delete_ticket(ticket: Ticket) -> None:
    await ticket.adelete()