from django.db import IntegrityError
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from projects.models import Project, ProjectMembership

from .models import Ticket
from .repository import create_ticket as create_ticket_repository
from .repository import delete_ticket as delete_ticket_repository
from .repository import (
    get_next_ticket_number,
    get_ticket_by_id,
    get_tickets_by_project,
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
        parent_epic = await get_ticket_by_id(parent_epic_id)
        if parent_epic is None:
            raise ValidationError('Parent epic not found.')
        if parent_epic.type != Ticket.Type.EPIC:
            raise ValidationError('parent_epic must be of type Epic.')
        if str(parent_epic.project_id) != str(project_id): # type: ignore (project_id is created by django as pointing to Project.id)
            raise ValidationError('Parent epic must belong to the same project.')
        return parent_epic
    return None

async def get_ticket_or_404(ticket_id: str) -> Ticket:
    ticket = await get_ticket_by_id(ticket_id)
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
        return await create_ticket_repository(title=title,
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
    
async def update_ticket(ticket: Ticket, requester_id: str, requester_role: ProjectMembership.Role, data: dict) -> Ticket:
    if not can_edit_ticket(ticket, requester_id, requester_role):
        raise PermissionDenied('You cannot edit this ticket') 
    if 'assignee_id' in data and data['assignee_id'] != requester_id and not can_assign_ticket(requester_role):
        raise PermissionDenied('Only Project Lead can assign tickets to others.')
    if 'story_points' in data:
        validate_story_point(data['story_points'])
    for key, value in data.items():
        setattr(ticket, key, value)
    try:
        await update_ticket_repository(ticket)
    except IntegrityError:
        raise ValidationError('A ticket with this key already exists.')
    return ticket

async def delete_ticket(ticket: Ticket) -> None:
    await delete_ticket_repository(ticket)

