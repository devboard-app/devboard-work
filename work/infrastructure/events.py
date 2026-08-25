import logging

from work.infrastructure.redis_client import redis_client

logger = logging.getLogger(__name__)
STREAM = "devboard:events"

async def publish_event(event: str, **kwargs) -> None:
    data = {"event": event, **kwargs}
    try:
        await redis_client.xadd(STREAM, {k: str(v) for k, v in data.items()})
    except Exception:
        logger.warning(f"Failed to publish event '{event}'", exc_info=True)
    
async def publish_ticket_assigned(ticket, actor_id: str, recipient_id: str) -> None:
    await publish_event(
        "ticket.assigned",
        project_id=ticket.project_id,
        actor_id=actor_id,
        recipient_id=recipient_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
    )

async def publish_ticket_unassigned(ticket, actor_id: str, previous_assignee_id: str) -> None:
    await publish_event(
        "ticket.unassigned",
        project_id=ticket.project_id,
        actor_id=actor_id,
        previous_assignee_id=previous_assignee_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
    )

async def publish_ticket_created(ticket, actor_id: str) -> None:
    await publish_event(
        "ticket.created",
        project_id=ticket.project_id,
        actor_id=actor_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
    )

async def publish_ticket_updated(ticket, actor_id: str, field: str, from_value: str, to_value: str | None) -> None:
    await publish_event(
        "ticket.updated",
        field=field,
        from_value=from_value,
        to_value=to_value,
        actor_id=actor_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
        project_id=ticket.project_id,
    )

async def publish_ticket_status_changed(ticket, actor_id: str, recipient_id: str, from_status: str, to_status: str) -> None:
    await publish_event(
        "ticket.status_changed",
        project_id=ticket.project_id,
        actor_id=actor_id,
        recipient_id=recipient_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
        from_status=from_status,
        to_status=to_status,
    )

async def publish_ticket_deleted(ticket, actor_id: str) -> None:
    await publish_event(
        "ticket.deleted",
        project_id=ticket.project_id,
        actor_id=actor_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
    )

async def publish_ticket_epic_linked(ticket, actor_id: str, epic_id: str, epic_key: str) -> None:
    await publish_event(
        "ticket.epic_linked",
        project_id=ticket.project_id,
        actor_id=actor_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
        epic_id=epic_id,
        epic_key=epic_key
    )

async def publish_ticket_epic_unlinked(ticket, actor_id: str, epic_id: str, epic_key: str) -> None:
    await publish_event(
        "ticket.epic_unlinked",
        project_id=ticket.project_id,
        actor_id=actor_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
        epic_id=epic_id,
        epic_key=epic_key
    )

async def publish_label_applied(ticket, label, actor_id: str) -> None:
    await publish_event(
        "label.applied",
        project_id=ticket.project_id,
        actor_id=actor_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
        label_id=label.id,
        label_name=label.name
    )

async def publish_label_removed(ticket, label, actor_id: str) -> None:
    await publish_event(
        "label.removed",
        project_id=ticket.project_id,
        actor_id=actor_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
        label_id=label.id,
        label_name=label.name
    )

async def publish_sprint_started(sprint, team_id: str, actor_id: str) -> None:
    await publish_event(
        "sprint.started",
        team_id=team_id,
        actor_id=actor_id,
        sprint_id=sprint.id,
        sprint_name=sprint.name,
        project_id=sprint.project_id,
    )

async def publish_sprint_completed(sprint, team_id: str, actor_id: str) -> None:
    await publish_event(
        "sprint.completed",
        team_id=team_id,
        actor_id=actor_id,
        sprint_id=sprint.id,
        sprint_name=sprint.name,
        project_id=sprint.project_id,
    )

async def publish_ticket_added_to_sprint(ticket, actor_id: str, sprint) -> None:
    await publish_event(
        "ticket.sprint_added",
        project_id=ticket.project_id,
        actor_id=actor_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
        sprint_id=sprint.id,
        sprint_name=sprint.name,
    )

async def publish_ticket_removed_from_sprint(ticket, actor_id: str, sprint) -> None:
    await publish_event(
        "ticket.sprint_removed",
        project_id=ticket.project_id,
        actor_id=actor_id,
        ticket_id=ticket.id,
        ticket_key=ticket.key,
        sprint_id=sprint.id,
        sprint_name=sprint.name,
    )