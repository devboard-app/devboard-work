from datetime import date

from projects.models import Project
from tickets.models import Ticket

from .models import Sprint


async def get_sprint_by_id(sprint_id: str, project_id: str) -> Sprint | None:
    return await Sprint.objects.filter(id=sprint_id, project_id=project_id).afirst()

async def get_sprints_by_project(project_id: str) -> list[Sprint]:
    return [m async for m in Sprint.objects.filter(project=project_id)]

async def get_active_sprint_by_project(project_id: str) -> Sprint | None:
    return await Sprint.objects.filter(project=project_id, status=Sprint.Status.ACTIVE).afirst()

async def create_sprint(name: str, goal: str, start_date: date | None, end_date: date | None, project: Project, created_by: str) -> Sprint:
    return await Sprint.objects.acreate(name=name,
                                        goal=goal,
                                        start_date=start_date,
                                        end_date=end_date,
                                        project=project,
                                        created_by=created_by)

async def update_sprint(sprint: Sprint) -> Sprint:
    await sprint.asave()
    return sprint

async def delete_sprint(sprint: Sprint) -> None:
    await sprint.adelete()

async def get_sprint_tickets(sprint: Sprint) -> list[Ticket]:
    return [m async for m in Ticket.objects.filter(sprint=sprint).prefetch_related('labels')]

async def sprint_has_tickets(sprint: Sprint) -> bool:
    return await Ticket.objects.filter(sprint=sprint).aexists()

async def get_sprint_tickets_page(sprint: Sprint, limit: int, offset: int) -> tuple[list[Ticket], int]:
    qs = Ticket.objects.filter(sprint=sprint).prefetch_related('labels')
    total = await qs.acount()
    return [t async for t in qs[offset:offset + limit]], total

async def move_unfinished_tickets_to_backlog(sprint: Sprint) -> None:
    await Ticket.objects.filter(sprint=sprint).exclude(status=Ticket.Status.DONE).aupdate(sprint=None, status=Ticket.Status.BACKLOG)
