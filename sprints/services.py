from rest_framework.exceptions import NotFound, ValidationError

from projects.models import Project
from tickets.models import Ticket
from tickets.repository import update_ticket
from work.infrastructure.events import (
    publish_sprint_completed,
    publish_sprint_started,
    publish_ticket_added_to_sprint,
    publish_ticket_removed_from_sprint,
)

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


async def get_sprint_or_404(sprint_id: str, project_id: str) -> Sprint:
    sprint = await get_sprint_by_id(sprint_id, project_id)
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
    allowed_fields = ['name', 'goal', 'start_date', 'end_date']
    filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
    if sprint.status != Sprint.Status.CREATED:
        raise ValidationError('You cannot edit Active or Completed sprints.')
    for key, value in filtered_data.items():
        setattr(sprint, key, value)
    return await update_sprint_repository(sprint)

async def delete_sprint(sprint: Sprint) -> None:
    if sprint.status != Sprint.Status.CREATED:
        raise ValidationError('You cannot delete Active or Completed sprints.')
    await delete_sprint_repository(sprint)

async def start_sprint(sprint: Sprint, project_id: str, team_id: str, actor_id: str) -> Sprint:
    if sprint.status != Sprint.Status.CREATED:
        raise ValidationError('You cannot start Active or Completed sprints.')
    if await get_active_sprint_by_project(project_id):
        raise ValidationError('There\'s already an active Sprint.')
    if not await get_sprint_tickets(sprint):
        raise ValidationError('Sprint must have at least one ticket.')
    sprint.status = Sprint.Status.ACTIVE
    sprint = await update_sprint_repository(sprint)
    try:
        await publish_sprint_started(sprint, team_id=team_id, actor_id=actor_id)
    except Exception: #noqa redis failure
        pass
    return sprint

async def complete_sprint(sprint: Sprint, team_id: str, actor_id: str) -> Sprint:
    if sprint.status != Sprint.Status.ACTIVE:
        raise ValidationError('You can only complete Active sprints.')
    await move_unfinished_tickets_to_backlog(sprint)
    sprint.status = Sprint.Status.COMPLETED
    sprint = await update_sprint_repository(sprint)
    try:
        await publish_sprint_completed(sprint, team_id=team_id, actor_id=actor_id)
    except Exception: #noqa redis failure
        pass
    return sprint

async def add_ticket_to_sprint(sprint: Sprint, ticket: Ticket, actor_id: str) -> None:
    if sprint.status == Sprint.Status.COMPLETED:
        raise ValidationError('You cannot add tickets to a completed sprint.')
    if sprint.project_id != ticket.project_id: #type: ignore
        raise ValidationError('Ticket does not belong to this project.')
    if ticket.sprint is not None:
        raise ValidationError('Ticket is already on another sprint.')
    ticket.sprint = sprint #type: ignore
    await update_ticket(ticket)
    try:
        await publish_ticket_added_to_sprint(ticket=ticket, actor_id=actor_id, sprint=sprint)
    except Exception: # noqa redis failure
        pass

async def remove_ticket_from_sprint(ticket: Ticket, sprint: Sprint, actor_id: str) -> None:
    ticket.sprint = None
    await update_ticket(ticket)
    try:
        await publish_ticket_removed_from_sprint(ticket=ticket, actor_id=actor_id, sprint=sprint)
    except Exception: # noqa redis failure
        pass

async def list_sprint_tickets(sprint: Sprint) -> list[Ticket]:
    return await get_sprint_tickets(sprint)
