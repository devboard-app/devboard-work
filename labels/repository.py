from projects.models import Project
from tickets.models import Ticket

from .models import Label


async def get_label_by_id(label_id: str) -> Label | None:
    return await Label.objects.filter(id=label_id).afirst()

async def get_labels_by_project(project_id: str) -> list[Label]:
    return [m async for m in Label.objects.filter(project=project_id)]

async def create_label(name: str, color: str, project: Project) -> Label:
    return await Label.objects.acreate(name=name, color=color, project=project)

async def update_label(label: Label) -> Label:
    await label.asave()
    return label

async def delete_label(label: Label) -> None:
    await label.adelete()

async def add_label_to_ticket(ticket: Ticket, label: Label) -> None:
    await ticket.labels.aadd(label)

async def remove_label_from_ticket(ticket: Ticket, label: Label) -> None:
    await ticket.labels.aremove(label)

async def get_ticket_labels(ticket: Ticket) -> list[Label]:
    return [m async for m in ticket.labels.all()]