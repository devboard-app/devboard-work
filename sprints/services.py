from django.db import IntegrityError
from rest_framework.exceptions import NotFound, ValidationError

from outbox.writer import awrite_with_outbox
from projects.models import Project
from tickets.models import Ticket
from tickets.repository import update_ticket_sync
from work.exceptions import Conflict
from work.infrastructure.events import build_payload

from .models import Sprint
from .repository import create_sprint as create_sprint_repository
from .repository import delete_sprint as delete_sprint_repository
from .repository import (
    get_active_sprint_by_project,
    get_sprint_by_id,
    get_sprint_tickets_page,
    get_sprints_by_project,
    move_unfinished_tickets_to_backlog_sync,
    sprint_has_tickets,
    update_sprint_sync,
)
from .repository import update_sprint as update_sprint_repository


async def get_sprint_or_404(sprint_id: str, project_id: str) -> Sprint:
    sprint = await get_sprint_by_id(sprint_id, project_id)
    if sprint is None:
        raise NotFound('Sprint not found.')
    return sprint

async def list_project_sprints(project_id: str, limit: int, offset: int) -> tuple[list[Sprint], int]:
    return await get_sprints_by_project(project_id, limit, offset)


async def create_sprint(project: Project, created_by: str, data: dict) -> Sprint:
    return await create_sprint_repository(data['name'], data['goal'], data.get('start_date'), data.get('end_date'), project, created_by)

async def update_sprint(sprint: Sprint, data: dict) -> Sprint:
    if sprint.status != Sprint.Status.CREATED:
        raise Conflict('You cannot edit Active or Completed sprints.')
    for key, value in data.items():
        setattr(sprint, key, value)
    return await update_sprint_repository(sprint)

async def delete_sprint(sprint: Sprint) -> None:
    if sprint.status != Sprint.Status.CREATED:
        raise Conflict('You cannot delete Active or Completed sprints.')
    await delete_sprint_repository(sprint)

async def start_sprint(sprint: Sprint, project_id: str, team_id: str, actor_id: str) -> Sprint:
    if sprint.status != Sprint.Status.CREATED:
        raise Conflict('You cannot start Active or Completed sprints.')
    if await get_active_sprint_by_project(project_id):
        raise Conflict('There\'s already an active Sprint.')
    if not await sprint_has_tickets(sprint):
        raise Conflict('Sprint must have at least one ticket.')
    sprint.status = Sprint.Status.ACTIVE
    payload = build_payload('sprint.started', team_id=team_id, actor_id=actor_id, sprint_id=sprint.id, sprint_name=sprint.name, project_id=sprint.project_id, # type: ignore
                            start_date=sprint.start_date.isoformat() if sprint.start_date else None, end_date=sprint.end_date.isoformat() if sprint.end_date else None)
    def _save():
        return update_sprint_sync(sprint)
    try:
        sprint = await awrite_with_outbox(_save, [('redis_stream', payload)])
    except IntegrityError:
        raise Conflict("There\'s already an active Sprint.")

    return sprint

async def complete_sprint(sprint: Sprint, team_id: str, actor_id: str) -> Sprint:
    if sprint.status != Sprint.Status.ACTIVE:
        raise Conflict('You can only complete Active sprints.')
    sprint.status = Sprint.Status.COMPLETED
    payload = build_payload('sprint.completed', team_id=team_id, actor_id=actor_id, sprint_id=sprint.id, sprint_name=sprint.name, project_id=sprint.project_id, # type: ignore
                            start_date=sprint.start_date.isoformat() if sprint.start_date else None, end_date=sprint.end_date.isoformat() if sprint.end_date else None)
    def _complete():
        move_unfinished_tickets_to_backlog_sync(sprint)
        return update_sprint_sync(sprint)
    
    sprint = await awrite_with_outbox(_complete, [('redis_stream', payload)])
    return sprint

async def add_ticket_to_sprint(sprint: Sprint, ticket: Ticket, actor_id: str) -> None:
    if sprint.status == Sprint.Status.COMPLETED:
        raise Conflict('You cannot add tickets to a completed sprint.')
    if sprint.project_id != ticket.project_id: #type: ignore
        raise ValidationError('Ticket does not belong to this project.')
    if ticket.sprint_id is not None: #type: ignore
        raise Conflict('Ticket is already on another sprint.')
    ticket.sprint = sprint #type: ignore
    payload = build_payload('ticket.sprint_added', project_id=ticket.project_id, actor_id=actor_id, ticket_id=ticket.id, ticket_key=ticket.key, sprint_id=sprint.id, sprint_name=sprint.name) # type: ignore

    def _save():
        return update_ticket_sync(ticket)
    await awrite_with_outbox(_save, [('redis_stream', payload)])

async def remove_ticket_from_sprint(ticket: Ticket, sprint: Sprint, actor_id: str) -> None:
    ticket.sprint = None
    payload = build_payload('ticket.sprint_removed', project_id=ticket.project_id, actor_id=actor_id, ticket_id=ticket.id, ticket_key=ticket.key, sprint_id=sprint.id, sprint_name=sprint.name) # type: ignore
    def _save():
        return update_ticket_sync(ticket)
    await awrite_with_outbox(_save, [('redis_stream', payload)])

async def list_sprint_tickets(sprint: Sprint, limit: int, offset: int) -> tuple[list[Ticket], int]:
    return await get_sprint_tickets_page(sprint, limit, offset)
