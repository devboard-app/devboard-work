from django.db import IntegrityError
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from tickets.models import Ticket
from tickets.services import can_edit_ticket

from .models import Label
from .repository import (
    add_label_to_ticket,
    get_label_by_id,
    get_labels_by_project,
)
from .repository import create_label as create_label_repository
from .repository import delete_label as delete_label_repository
from .repository import get_ticket_labels as get_ticket_labels_repository
from .repository import remove_label_from_ticket as remove_label_from_ticket_repository
from .repository import update_label as update_label_repository


async def get_label_or_404(label_id: str) -> Label:
    label = await get_label_by_id(label_id)
    if label is None:
        raise NotFound('Label not found')
    return label

async def list_project_labels(project_id: str) -> list[Label]:
    return await get_labels_by_project(project_id)

async def create_label(project, data) -> Label:
    name = data.get('name')
    color = data.get('color', '#6B7280') #neutral grey
    if name is None:
        raise ValidationError('Name is required.')
    try:
        return await create_label_repository(name=name, color=color, project=project)
    except IntegrityError:
        raise ValidationError('A label with this name already exists in this project.')

async def update_label(label: Label, data: dict) -> Label:
    for key, value in data.items():
        setattr(label, key, value)
    try:
        return await update_label_repository(label=label)
    except IntegrityError:
        raise ValidationError('A label with this name already exists in this project.')

async def delete_label(label: Label) -> None:
    await delete_label_repository(label)

async def apply_label_to_ticket(ticket: Ticket, label: Label, requester_id: str, requester_role: str) -> None:
    if not can_edit_ticket(ticket, requester_id, requester_role):
        raise PermissionDenied('You cannot edit this ticket')
    if str(ticket.project_id) != str(label.project_id): # type: ignore (project_id is created by django as pointing to Project.id)
        raise ValidationError('Label does not belong to the same project as the ticket.')
    await add_label_to_ticket(ticket, label)

async def remove_label_from_ticket(ticket: Ticket, label: Label, requester_id: str, requester_role: str) -> None:
    if not can_edit_ticket(ticket, requester_id, requester_role):
        raise PermissionDenied('You cannot edit this ticket')
    await remove_label_from_ticket_repository(ticket, label)

async def get_ticket_labels(ticket: Ticket) -> list[Label]:
    return await get_ticket_labels_repository(ticket)