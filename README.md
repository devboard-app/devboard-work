# devboard-work

Work management microservice for the DevBoard platform. Handles teams, projects,
tickets, labels, sprints and comments, and publishes domain events to Redis.

## Stack

- **Django** — web framework
- **Django REST Framework** — API layer (async views via a custom `AsyncAPIView`)
- **PostgreSQL** — database
- **Redis Streams** — publishes domain events to `devboard:events`
- **python-jose** — JWT decoding
- **httpx** — calls devboard-core, devboard-email and devboard-attachments
- **whitenoise** — static file serving

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Debug mode (`True`/`False`) |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL user |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | PostgreSQL host (default: `localhost`) |
| `DB_PORT` | PostgreSQL port (default: `5432`) |
| `INTERNAL_API_KEY` | Shared secret for internal service calls |
| `JWT_SECRET` | Secret for verifying JWTs issued by devboard-auth |
| `CORE_SERVICE_URL` | URL of devboard-core (user lookups) |
| `EMAIL_SERVICE_URL` | URL of devboard-email (team invitations) |
| `ATTACHMENTS_SERVICE_URL` | URL of devboard-attachments (file metadata) |
| `REDIS_URL` | Redis connection string for the event stream |

## Running with Docker

```bash
docker compose up --build -d
docker compose exec devboard-work python manage.py migrate
docker compose down
```

The container has no bind mount, so code changes require a rebuild.

## Roles

Two independent role systems:

- **Team roles** — `owner`, `admin`, `member`, `viewer`
- **Project roles** — `lead`, `contributor`

Every endpoint checks the team role first, then the project role. Being on a team does
not grant access to its projects — project membership is separate.

## API

Base path: `/api/teams`. All endpoints require `Authorization: Bearer <jwt>`.

### Teams

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/teams/` | List teams you belong to |
| `POST` | `/api/teams/` | Create a team |
| `GET` | `/api/teams/<team_id>/` | Team detail |
| `PATCH` | `/api/teams/<team_id>/` | Update a team |
| `DELETE` | `/api/teams/<team_id>/` | Delete a team |
| `GET` | `/api/teams/<team_id>/members/` | List members |
| `POST` | `/api/teams/<team_id>/members/` | Add a member by email |
| `PATCH` | `/api/teams/<team_id>/members/<user_id>/` | Change a member's role |
| `DELETE` | `/api/teams/<team_id>/members/<user_id>/` | Remove a member |
| `DELETE` | `/api/teams/<team_id>/members/me/` | Leave the team |

### Projects

Prefix: `/api/teams/<team_id>/projects`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | List projects in the team |
| `POST` | `/` | Create a project |
| `GET` | `/<project_id>/` | Project detail |
| `PATCH` | `/<project_id>/` | Update a project |
| `DELETE` | `/<project_id>/` | Delete a project |
| `GET` | `/<project_id>/members/` | List project members |
| `POST` | `/<project_id>/members/` | Add a project member |
| `PATCH` | `/<project_id>/members/<user_id>/` | Change a project role |
| `DELETE` | `/<project_id>/members/<user_id>/` | Remove a project member |
| `GET` | `/<project_id>/board/` | Tickets grouped by status |
| `GET` | `/<project_id>/backlog/` | Tickets not in a sprint |

### Tickets

Prefix: `/api/teams/<team_id>/projects/<project_id>/tickets`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | List tickets |
| `POST` | `/` | Create a ticket |
| `GET` | `/<ticket_id>/` | Ticket detail |
| `PATCH` | `/<ticket_id>/` | Update a ticket |
| `DELETE` | `/<ticket_id>/` | Delete a ticket |

### Labels

Prefix: `/api/teams/<team_id>/projects/<project_id>`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/labels/` | List project labels |
| `POST` | `/labels/` | Create a label |
| `GET` | `/labels/<label_id>/` | Label detail |
| `PATCH` | `/labels/<label_id>/` | Update a label |
| `DELETE` | `/labels/<label_id>/` | Delete a label |
| `GET` | `/tickets/<ticket_id>/labels/` | Labels on a ticket |
| `POST` | `/tickets/<ticket_id>/labels/` | Apply a label to a ticket |
| `DELETE` | `/tickets/<ticket_id>/labels/<label_id>/` | Remove a label from a ticket |

### Sprints

Prefix: `/api/teams/<team_id>/projects/<project_id>/sprints`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | List sprints |
| `POST` | `/` | Create a sprint |
| `GET` | `/<sprint_id>/` | Sprint detail |
| `PATCH` | `/<sprint_id>/` | Update a sprint |
| `DELETE` | `/<sprint_id>/` | Delete a sprint |
| `POST` | `/<sprint_id>/start/` | Start a sprint |
| `POST` | `/<sprint_id>/complete/` | Complete a sprint |
| `GET` | `/<sprint_id>/tickets/` | Tickets in the sprint |
| `POST` | `/<sprint_id>/tickets/` | Add a ticket to the sprint |
| `DELETE` | `/<sprint_id>/tickets/<ticket_id>/` | Remove a ticket from the sprint |

### Comments

Prefix: `/api/teams/<team_id>/projects/<project_id>/tickets/<ticket_id>/comments`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | List comments on a ticket |
| `POST` | `/` | Add a comment |
| `PATCH` | `/<comment_id>/` | Edit your own comment |
| `DELETE` | `/<comment_id>/` | Delete your own comment (project leads can delete any) |

Comments support file attachments and `@` mentions — see below.

### Internal

Service-to-service only, authenticated with `X-Service-Key`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/internal/teams/<team_id>/members/<user_id>/` | Check team membership |
| `GET` | `/api/internal/projects/<project_id>/tickets/<key>/` | Look up a ticket by key |

## Comments

### Attachments

Files live in devboard-attachments. A comment stores `attachment_ids` only. When a
comment is rendered, work calls the attachments batch endpoint to resolve them into
`{id, filename, content_type, size, url}` and returns them as `attachments`.

List requests resolve every id on the page in one call. If devboard-attachments is
unavailable the comment is still returned, with an empty `attachments` array.

### Mentions

`@username` in a comment body is parsed, resolved to a user id via devboard-core's
`/api/users/lookup/`, and stored in `mentioned_user_ids`.

Dropped without error:

- usernames that do not exist
- the comment author mentioning themselves
- users who are not members of the project

Editing a comment rebuilds the list from the new body, and only newly added mentions
produce a notification.

## Events

Published to the Redis stream `devboard:events`. Consumed by devboard-analytics for the
activity log and by devboard-integrations for notifications.

| Event | Notes |
|---|---|
| `ticket.created` | |
| `ticket.updated` | carries `field`, `from_value`, `to_value` |
| `ticket.assigned` | carries `recipient_id` |
| `ticket.unassigned` | |
| `ticket.status_changed` | carries `recipient_id` |
| `ticket.deleted` | |
| `ticket.epic_linked` / `ticket.epic_unlinked` | |
| `ticket.sprint_added` / `ticket.sprint_removed` | |
| `label.applied` / `label.removed` | |
| `sprint.started` / `sprint.completed` | |
| `comment.created` | carries `recipient_id` when the ticket has an assignee to notify |
| `comment.updated` / `comment.deleted` | |
| `comment.mentioned` | one event per mentioned user, each with `recipient_id` |

Events carrying `recipient_id` become notifications. Publishing failures are logged and
swallowed, so a Redis outage never fails the request that caused the event.

## Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```
