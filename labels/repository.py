from projects.models import Project
from tickets.models import Ticket
from work.pagination import page

from .models import Label


async def get_label_by_id(label_id: str, project_id: str) -> Label | None:
    return await Label.objects.filter(id=label_id, project_id=project_id).afirst()

async def get_labels_by_project(project_id: str, limit: int, offset: int) -> tuple[list[Label], int]:
    return await page(Label.objects.filter(project=project_id), limit, offset)

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

async def get_ticket_labels(ticket: Ticket, limit: int, offset: int) -> tuple[list[Label], int]:
    return await page(Label.objects.filter(tickets=ticket), limit, offset)