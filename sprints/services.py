from asgiref.sync import sync_to_async
from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from projects.models import Project
from tickets.models import Ticket
from tickets.repository import update_ticket

from .models import Sprint
from .repository import create_sprint as create_sprint_repository
from .repository import delete_sprint as delete_sprint_repository
from .repository import (
    get_active_sprint_by_project,
    get_sprint_by_id,
    get_sprint_tickets,
    get_sprints_by_project,
    move_unfinished_tickets_to_backlog,
)
from .repository import update_sprint as update_sprint_repository

atomic = sync_to_async(transaction.atomic)

async def get_sprint_or_404(sprint_id: str) -> Sprint:
    sprint = await get_sprint_by_id(sprint_id)
    if sprint is None:
        raise NotFound('Sprint not found.')
    return sprint

async def list_project_sprints(project_id: str) -> list[Sprint]:
    return  await get_sprints_by_project(project_id)


async def create_sprint(project: Project, created_by: str, data: dict) -> Sprint:
    name = data.get('name')
    if name is None:
        raise ValidationError('Name is required.')
    goal = data.get('goal', '')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    return await create_sprint_repository(name, goal, start_date, end_date, project, created_by)

async def update_sprint(sprint: Sprint, data: dict) -> Sprint:
    if sprint.status != Sprint.Status.CREATED:
        raise ValidationError('You cannot edit Active or Completed sprints.')
    for key, value in data.items():
        setattr(sprint, key, value)
    return await update_sprint_repository(sprint)

async def delete_sprint(sprint: Sprint) -> None:
    if sprint.status != Sprint.Status.CREATED:
        raise ValidationError('You cannot delete Active or Completed sprints.')
    await delete_sprint_repository(sprint)

async def start_sprint(sprint: Sprint, project_id: str) -> Sprint:
    if sprint.status != Sprint.Status.CREATED:
        raise ValidationError('You cannot start Active or Completed sprints.')
    if await get_active_sprint_by_project(project_id):
        raise ValidationError('There\'s already an active Sprint.')
    if not await get_sprint_tickets(sprint):
        raise ValidationError('Sprint must have at least one ticket.')
    sprint.status = Sprint.Status.ACTIVE
    sprint = await update_sprint_repository(sprint)
    return sprint

async def complete_sprint(sprint: Sprint) -> Sprint:
    if sprint.status != Sprint.Status.ACTIVE:
        raise ValidationError('You can only complete Active sprints.')
    with await atomic():
        await move_unfinished_tickets_to_backlog(sprint)
        sprint.status = Sprint.Status.COMPLETED
        return await update_sprint_repository(sprint)

async def add_ticket_to_sprint(sprint: Sprint, ticket: Ticket) -> None:
    if sprint.status == Sprint.Status.COMPLETED:
        raise ValidationError('You cannot add tickets to a completed sprint.')
    if sprint.project != ticket.project:
        raise ValidationError('Ticket does not belong to this project.')
    if ticket.sprint is not None:
        raise ValidationError('Ticket is already on another sprint.')
    ticket.sprint = sprint #type: ignore
    await update_ticket(ticket)

async def remove_ticket_from_sprint(ticket: Ticket) -> None:
    ticket.sprint = None
    await update_ticket(ticket)

async def list_sprint_tickets(sprint: Sprint) -> list[Ticket]:
    return await get_sprint_tickets(sprint)
    