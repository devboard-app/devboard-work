from django.db import IntegrityError
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from projects.models import Project, ProjectMembership
from sprints.repository import get_active_sprint_by_project, get_sprint_tickets
from work.infrastructure.events import (
    publish_ticket_assigned,
    publish_ticket_created,
    publish_ticket_deleted,
    publish_ticket_epic_linked,
    publish_ticket_epic_unlinked,
    publish_ticket_status_changed,
    publish_ticket_unassigned,
    publish_ticket_updated,
)

from .models import Ticket
from .repository import create_ticket as create_ticket_repository
from .repository import delete_ticket as delete_ticket_repository
from .repository import (
    get_next_ticket_number,
    get_ticket_by_id,
    get_tickets_by_project,
    get_tickets_by_project_and_no_sprint,
)
from .repository import update_ticket as update_ticket_repository

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

async def list_project_tickets(project_id: str) -> list[Ticket]:
    return await get_tickets_by_project(project_id)

async def create_ticket(project: Project, created_by: str, requester_role: ProjectMembership.Role, data: dict) -> Ticket:
    title = data.get('title')
    type = data.get('type')
    story_points = data.get('story_points')
    if title is None:
        raise ValidationError('Title is required.')
    if type is None:
        raise ValidationError('Type is required.')
    if story_points:
        validate_story_point(story_points)
    description = data.get('description', '')
    priority = data.get('priority', Ticket.Priority.MEDIUM)
    status = data.get('status', Ticket.Status.BACKLOG)
    assignee_id = data.get('assignee_id')
    parent_epic_id = data.get('parent_epic')
    due_date = data.get('due_date')

    parent_epic = await _validate_epic_rules(ticket_type=type, project_id=str(project.id), requester_role=requester_role, assignee_id=assignee_id, parent_epic_id=parent_epic_id)
    ticket_number = await get_next_ticket_number(str(project.id))
    key = f'{project.key}-{ticket_number}'
    try:
        ticket = await create_ticket_repository(title=title,
                                        description=description,
                                        type=type,
                                        priority=priority,
                                        status=status,
                                        project=project,
                                        created_by=created_by,
                                        ticket_number=ticket_number,
                                        key=key,
                                        assignee_id= assignee_id,
                                        parent_epic=parent_epic,
                                        due_date=due_date)
    except IntegrityError:
        raise ValidationError('Something went wrong, please try again.')
    
    try:
        await publish_ticket_created(ticket, actor_id=created_by)

        if assignee_id:
            await publish_ticket_assigned(ticket, actor_id=created_by, recipient_id=assignee_id)
    except Exception: #noqa redis failure
        pass    

    return ticket
    
async def update_ticket(ticket: Ticket, requester_id: str, requester_role: ProjectMembership.Role, data: dict) -> Ticket:
    allowed_fields = ['title', 'description', 'type', 'priority', 'status', 'assignee_id', 'story_points', 'parent_epic', 'due_date']
    filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
    if not can_edit_ticket(ticket, requester_id, requester_role):
        raise PermissionDenied('You cannot edit this ticket') 
    if 'assignee_id' in filtered_data and filtered_data['assignee_id'] != requester_id and not can_assign_ticket(requester_role):
        raise PermissionDenied('Only Project Lead can assign tickets to others.')
    if 'story_points' in filtered_data:
        validate_story_point(filtered_data['story_points'])

    old_snapshot= _snapshot_ticket(ticket)

    for key, value in filtered_data.items():
        setattr(ticket, key, value)
    try:
        await update_ticket_repository(ticket)
    except IntegrityError:
        raise ValidationError('A ticket with this key already exists.')

    await _publish_ticket_update_events(ticket, requester_id, filtered_data, old_snapshot)
    return ticket

async def delete_ticket(ticket: Ticket, requester_id: str) -> None:
    try:
        await publish_ticket_deleted(ticket, actor_id=requester_id)
    except Exception: # noqa redis failure
        pass
    await delete_ticket_repository(ticket)

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

async def get_backlog(project_id: str) -> list[Ticket]:
    return await get_tickets_by_project_and_no_sprint(project_id)


def _snapshot_ticket(ticket: Ticket) -> dict:
    return {
        'assignee_id': str(ticket.assignee_id) if ticket.assignee_id else None,
        'status': ticket.status,
        'title': ticket.title,
        'description': ticket.description,
        'parent_epic_id': str(ticket.parent_epic_id) if ticket.parent_epic_id else None, # type:ignore
    }

async def _publish_ticket_update_events(ticket: Ticket, requester_id: str, filtered_data: dict, old: dict) -> None:
    new_assignee_id = filtered_data.get('assignee_id')
    new_epic_id = filtered_data.get('parent_epic')
    new_parent_epic = await get_ticket_by_id(new_epic_id, str(ticket.project_id)) if new_epic_id else None #type: ignore

    try:
        if 'title' in filtered_data and old['title'] != filtered_data.get('title'):
            await publish_ticket_updated(ticket, actor_id=requester_id, field='title', from_value=old['title'], to_value=filtered_data['title'])

        if 'description' in filtered_data and old['description'] != filtered_data.get('description'):
            await publish_ticket_updated(ticket, actor_id=requester_id, field='description', from_value=old['description'], to_value=filtered_data['description'])

        if new_assignee_id and new_assignee_id != old['assignee_id']:
            await publish_ticket_assigned(ticket, actor_id=requester_id, recipient_id=new_assignee_id)

        if 'assignee_id' in filtered_data and new_assignee_id is None and old['assignee_id']:
            await publish_ticket_unassigned(ticket, actor_id=requester_id, previous_assignee_id=old['assignee_id'])

        if 'status' in filtered_data and filtered_data['status'] != old['status'] and ticket.assignee_id:
            await publish_ticket_status_changed(ticket, actor_id=requester_id, recipient_id=str(ticket.assignee_id), from_status=old['status'], to_status=ticket.status)

        if new_parent_epic and str(new_parent_epic.id) != old['parent_epic_id']:
            await publish_ticket_epic_linked(ticket, actor_id=requester_id, epic_id=str(new_parent_epic.id), epic_key=new_parent_epic.key)

        if old['parent_epic_id'] and new_parent_epic is None and 'parent_epic' in filtered_data:
            old_parent_epic = await get_ticket_by_id(old['parent_epic_id'], str(ticket.project_id)) #type: ignore
            if old_parent_epic:
                await publish_ticket_epic_unlinked(ticket, actor_id=requester_id, epic_id=old['parent_epic_id'], epic_key=old_parent_epic.key)

    except Exception: # noqa redis failure
        pass