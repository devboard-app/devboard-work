from work.infrastructure.redis_client import redis_client

STREAM = "devboard:events"

async def publish_event(event: str, **kwargs) -> None:
    data = {"event": event, **kwargs}
    await redis_client.xadd(STREAM, {k: str(v) for k, v in data.items()})

async def publish_ticket_assigned(ticket, actor_id: str, recipient_id: str) -> None:
    await publish_event(
        "ticket.assigned",
        project_id=ticket.project_id,
        actor_id=actor_id,
        recipient_id=recipient_id,
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

async def publish_sprint_started(sprint, team_id: str, actor_id: str, from_status: str, to_status: str) -> None:
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