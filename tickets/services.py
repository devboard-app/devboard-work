import logging
import uuid

from django.db import IntegrityError
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from outbox.writer import awrite_with_outbox
from projects.models import Project, ProjectMembership
from sprints.repository import get_active_sprint_by_project, get_sprint_tickets
from work.exceptions import APIException, Conflict
from work.infrastructure.events import (
    build_payload,
)

from .models import Ticket
from .repository import (
    create_ticket_sync,
    delete_ticket_sync,
    get_next_ticket_number,
    get_ticket_by_id,
    get_tickets_by_project,
    get_tickets_by_project_and_no_sprint,
    update_ticket_sync,
)

logger = logging.getLogger(__name__)
Role = ProjectMembership.Role

def can_edit_ticket(ticket: Ticket, requester_id: str, requester_role: str) -> bool:
    return requester_role == Role.LEAD or (requester_role == Role.CONTRIBUTOR and str(ticket.assignee_id) == requester_id)

def can_assign_ticket(requester_role) -> bool:
    return requester_role == Role.LEAD

def validate_story_point(story_points: int) -> None:
    if story_points not in [1, 2, 3, 5, 8, 13, 21]:
        raise ValidationError('Story point must be a Fibonacci number: 1, 2, 3, 5, 8, 13, 21.')

async def _validate_epic_rules(ticket_type: Ticket.Type, project_id: str, requester_role: Role, assignee_id: str | None, parent_epic_id: str | None) -> Ticket | None:
    if ticket_type == Ticket.Type.EPIC:
        if requester_role != Role.LEAD:
            raise PermissionDenied('Only project Lead can create an Epic.')
        if assignee_id is not None:
            raise ValidationError('Epic cannot have an assignee.')
        if parent_epic_id is not None:
            raise ValidationError('Epic cannot have a parent epic.')
        return None
    if parent_epic_id:
        parent_epic = await get_ticket_by_id(parent_epic_id, project_id)
        if parent_epic is None:
            raise ValidationError('Parent epic not found.')
        if parent_epic.type != Ticket.Type.EPIC:
            raise ValidationError('parent_epic must be of type Epic.')
        return parent_epic
    return None

async def get_ticket_or_404(ticket_id: str, project_id: str) -> Ticket:
    ticket = await get_ticket_by_id(ticket_id, project_id)
    if ticket is None:
        raise NotFound('Ticket not found.')
    return ticket

async def list_project_tickets(project_id: str, limit: int, offset: int) -> tuple[list[Ticket], int]:
    return await get_tickets_by_project(project_id, limit, offset)

@retry(retry = retry_if_exception_type(IntegrityError), stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=0.05, max=0.5), reraise=True)
async def _create_ticket_with_number(project, title, description, type, priority, status, created_by, assignee_id, parent_epic, due_date, story_points) -> Ticket:
    ticket_number = await get_next_ticket_number(str(project.id))
    key = f'{project.key}-{ticket_number}'
    ticket_id = uuid.uuid4()
    events = [('redis_stream', build_payload('ticket.created', project_id=project.id, actor_id=created_by, ticket_id=ticket_id, ticket_key=key, story_points=story_points, status=status))]
    if assignee_id:
        events.append(('redis_stream', build_payload('ticket.assigned', project_id=project.id, actor_id=created_by, recipient_id=assignee_id, ticket_id=ticket_id, ticket_key=key)))

    def _create():
        return create_ticket_sync(
            id=ticket_id, title=title, description=description, type=type, priority=priority, status=status,
            project=project, created_by=created_by, ticket_number=ticket_number, key=key,
            assignee_id=assignee_id, parent_epic=parent_epic, due_date=due_date, story_points=story_points
        )
    return await awrite_with_outbox(_create, events)

async def create_ticket(project: Project, created_by: str, requester_role: ProjectMembership.Role, data: dict) -> Ticket:
    title = data['title']
    type = data['type']
    description = data['description']
    priority = data['priority']
    status = data['status']
    story_points = data.get('story_points')
    assignee_id = data.get('assignee_id')
    parent_epic_id = data.get('parent_epic')
    due_date = data.get('due_date')

    parent_epic = await _validate_epic_rules(ticket_type=type, project_id=str(project.id), requester_role=requester_role, assignee_id=assignee_id, parent_epic_id=parent_epic_id)

    try:
        ticket = await _create_ticket_with_number(project, title, description, type, priority, status, created_by, assignee_id, parent_epic, due_date, story_points)
    except IntegrityError:
        logger.exception(f"Could not allocate a ticket number for project {project.key} after 5 attempts")
        raise APIException("Could not allocate a ticket number, please retry.")
        
    return ticket
    

async def update_ticket(ticket: Ticket, requester_id: str, requester_role: ProjectMembership.Role, data: dict) -> Ticket:
    if not can_edit_ticket(ticket, requester_id, requester_role):
        raise PermissionDenied('You cannot edit this ticket') 
    if 'assignee_id' in data and str(data['assignee_id']) != requester_id and not can_assign_ticket(requester_role):
        raise PermissionDenied('Only Project Lead can assign tickets to others.')

    old_snapshot= _snapshot_ticket(ticket)

    if 'parent_epic' in data:
        epic_id = data['parent_epic']
        if epic_id:
            parent_epic = await get_ticket_by_id(epic_id, str(ticket.project_id)) #type: ignore
            if parent_epic is None:
                raise ValidationError('Parent epic not found.')
            if parent_epic.type != Ticket.Type.EPIC:
                raise ValidationError('parent_epic must be of type Epic.')
            data['parent_epic'] = parent_epic
        else:
            data['parent_epic'] = None

    old_parent_epic = None
    if old_snapshot['parent_epic_id'] and data.get('parent_epic') is None and 'parent_epic' in data:
        old_parent_epic = await get_ticket_by_id(old_snapshot['parent_epic_id'], str(ticket.project_id)) # type: ignore

    for key, value in data.items():
        setattr(ticket, key, value)

    events = _build_ticket_update_events(ticket, requester_id, data, old_snapshot, old_parent_epic)

    def _save():
        return update_ticket_sync(ticket)
    try:
        await awrite_with_outbox(_save, events)
    except IntegrityError:
        raise Conflict('A ticket with this key already exists.')

    return ticket

async def delete_ticket(ticket: Ticket, requester_id: str) -> None:
    project_id, ticket_id, ticket_key = ticket.project_id, ticket.id, ticket.key #type: ignore
    payload = build_payload('ticket.deleted', project_id=project_id, actor_id=requester_id, ticket_id=ticket_id, ticket_key=ticket_key)
    def _delete():
        return delete_ticket_sync(ticket)
    await awrite_with_outbox(_delete, [('redis_stream', payload)])

async def get_board(project_id: str) -> dict:
    sprint = await get_active_sprint_by_project(project_id)
    if sprint is None:
        return {'sprint': None, 'board': {}}
    tickets = await get_sprint_tickets(sprint)
    board = {
        'backlog': [],
        'todo': [],
        'in_progress': [],
        'in_review': [],
        'done' :[],
    }
    for ticket in tickets:
        board[ticket.status].append(ticket)
    return {'sprint': sprint, 'board': board}

async def get_backlog(project_id: str, limit: int, offset: int) -> tuple[list[Ticket],int]:
    return await get_tickets_by_project_and_no_sprint(project_id, limit, offset)


def _snapshot_ticket(ticket: Ticket) -> dict:
    return {
        'assignee_id': str(ticket.assignee_id) if ticket.assignee_id else None,
        'status': ticket.status,
        'title': ticket.title,
        'description': ticket.description,
        'parent_epic_id': str(ticket.parent_epic_id) if ticket.parent_epic_id else None, # type:ignore
        'priority': ticket.priority,
        'type': ticket.type,
        'due_date': ticket.due_date.isoformat() if ticket.due_date else None,
        'story_points': ticket.story_points
    }

def _build_ticket_update_events(ticket: Ticket, requester_id: str, data: dict, old: dict, old_parent_epic: Ticket | None) -> list[tuple[str, dict]]:
    new_assignee_id = str(data['assignee_id']) if data.get('assignee_id') else None
    new_due_date = data['due_date'].isoformat() if data.get('due_date') else None
    new_parent_epic = data.get('parent_epic')

    events: list[tuple[str, dict]] = []

    def add(event, **kwargs):
        events.append(('redis_stream', build_payload(event, **kwargs)))

    if 'title' in data and old['title'] != data.get('title'):
        add('ticket.updated', field='title', from_value=old['title'], to_value=data['title'], actor_id=requester_id, ticket_id=ticket.id, ticket_key=ticket.key, project_id=ticket.project_id) # type: ignore

    if 'description' in data and old['description'] != data.get('description'):
        add('ticket.updated', field='description', from_value=old['description'], to_value=data['description'], actor_id=requester_id, ticket_id=ticket.id, ticket_key=ticket.key, project_id=ticket.project_id) # type: ignore

    if 'priority' in data and old['priority'] != data.get('priority'):
        add('ticket.updated', field='priority', from_value=old['priority'], to_value=data['priority'], actor_id=requester_id, ticket_id=ticket.id, ticket_key=ticket.key, project_id=ticket.project_id) # type: ignore

    if 'type' in data and old['type'] != data.get('type'):
        add('ticket.updated', field='type', from_value=old['type'], to_value=data['type'], actor_id=requester_id, ticket_id=ticket.id, ticket_key=ticket.key, project_id=ticket.project_id) # type: ignore

    if 'due_date' in data and old['due_date'] != new_due_date:
        add('ticket.updated', field='due_date', from_value=old['due_date'], to_value=new_due_date, actor_id=requester_id, ticket_id=ticket.id, ticket_key=ticket.key, project_id=ticket.project_id) # type: ignore

    if 'story_points' in data and old['story_points'] != data.get('story_points'):
        add('ticket.updated', field='story_points', from_value=old['story_points'], to_value=data['story_points'], actor_id=requester_id, ticket_id=ticket.id, ticket_key=ticket.key, project_id=ticket.project_id) # type: ignore

    if new_assignee_id and new_assignee_id != old['assignee_id']:
        add('ticket.assigned', project_id=ticket.project_id, actor_id=requester_id, recipient_id=new_assignee_id, ticket_id=ticket.id, ticket_key=ticket.key) # type: ignore

    if 'assignee_id' in data and new_assignee_id is None and old['assignee_id']:
        add('ticket.unassigned', project_id=ticket.project_id, actor_id=requester_id, previous_assignee_id=old['assignee_id'], ticket_id=ticket.id, ticket_key=ticket.key) # type: ignore

    if 'status' in data and data['status'] != old['status']:
        add('ticket.status_changed', project_id=ticket.project_id, actor_id=requester_id, recipient_id=str(ticket.assignee_id) if ticket.assignee_id else None, ticket_id=ticket.id, ticket_key=ticket.key, from_status=old['status'], to_status=ticket.status) # type: ignore

    if new_parent_epic and str(new_parent_epic.id) != old['parent_epic_id']:
        add('ticket.epic_linked', project_id=ticket.project_id, actor_id=requester_id, ticket_id=ticket.id, ticket_key=ticket.key, epic_id=str(new_parent_epic.id), epic_key=new_parent_epic.key) # type: ignore
    if old_parent_epic:
        add('ticket.epic_unlinked', project_id=ticket.project_id, actor_id=requester_id, ticket_id=ticket.id, ticket_key=ticket.key, epic_id=old['parent_epic_id'], epic_key=old_parent_epic.key) # type: ignore

    return events