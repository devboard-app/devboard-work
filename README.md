# devboard-work

**The heart of DevBoard.** Teams, projects, tickets, labels, sprints and comments all live here. Every change also sends an event to the rest of the system.

- **Port:** `8004`
- **Stack:** Django, Django REST Framework (async views), PostgreSQL, Redis Streams
- **Two containers, one image:** the API, and an **outbox relay** that delivers events (see "Events").

---

## Start here (about 5 minutes)

1. Open a terminal in `devboard-infra`.
2. Run `setup.bat`. It creates the database, starts both containers and runs the migrations.
3. Open `http://localhost:8004/api/teams/`. It answers `401`, which means the service is up and wants a login.

Only want this service? The database and Redis must already be running. Then:

```bash
docker compose up --build -d
docker compose exec devboard-work python manage.py migrate
```

There is no bind mount, so after a code change you must rebuild.

---

## What it does

1. **Teams** – create a team, add people by email, give them roles.
2. **Projects** – live inside a team. Each has a short key like `DEV`.
3. **Tickets** – the work items. Keys look like `DEV-12`.
4. **Sprints** – time boxes. Start one, finish one.
5. **Labels and comments** – tag tickets, talk about them, attach files, `@mention` people.

---

## How it fits

```
Browser ──JWT──> devboard-work ──> PostgreSQL
                      │
                      ├── outbox ──> Redis stream ──> analytics, integrations
                      ├── outbox ──> devboard-email      (team invitations)
                      ├──> devboard-core               (find users by name or email)
                      └──> devboard-attachments        (turn file ids into links)

analytics, integrations ──X-Service-Key──> devboard-work  (who is on which team or project)
```

Every authenticated request checks the caller's account status with devboard-core. That result is cached in Redis for 60 seconds, so core being slow or briefly down doesn't slow down or fail every request here — a deactivated user is blocked within 60 seconds instead of immediately.

---

## Roles

Two separate systems. Every endpoint checks the team role first, then the project role.

| Level | Roles |
|---|---|
| Team | `owner`, `admin`, `member`, `viewer` |
| Project | `lead`, `contributor` |

Being on a team does **not** give access to its projects. Project membership is separate.

---

## Tickets

| Field | Values |
|---|---|
| `type` | `epic`, `bug`, `feature`, `task`, `improvement` |
| `priority` | `low`, `medium`, `high`, `critical` |
| `status` | `backlog`, `todo`, `in_progress`, `in_review`, `done` |
| Other | `title`, `description`, `assignee_id`, `due_date`, `story_points`, `parent_epic`, labels, sprint |

The key is the project key plus a number: `DEV-1`, `DEV-2`, and so on.

## Sprint rules

- A project can have **one** active sprint.
- Only a sprint that has not started can be edited, deleted or started.
- A sprint needs **at least one ticket** to start.
- A ticket can be in **one** sprint at a time.
- Only an active sprint can be completed.

---

## API

All routes need `Authorization: Bearer <jwt>`. List routes use `limit` and `offset`.
Paths below are shortened. `{P}` means `/api/teams/<team_id>/projects/<project_id>`.

### Teams

| Method | Path | What it does |
|---|---|---|
| `GET` `POST` | `/api/teams/` | List your teams, create a team. |
| `GET` `PATCH` `DELETE` | `/api/teams/<team_id>/` | Read, update, delete a team. |
| `GET` `POST` | `/api/teams/<team_id>/members/` | List members, add one by email (sends an invitation mail). |
| `PATCH` `DELETE` | `/api/teams/<team_id>/members/<user_id>/` | Change a role, remove a member. |
| `DELETE` | `/api/teams/<team_id>/members/me/` | Leave the team. |

### Projects

| Method | Path | What it does |
|---|---|---|
| `GET` `POST` | `/api/teams/<team_id>/projects/` | List, create. |
| `GET` `PATCH` `DELETE` | `{P}/` | Read, update, delete. |
| `GET` `POST` | `{P}/members/` | List, add a project member. |
| `PATCH` `DELETE` | `{P}/members/<user_id>/` | Change a project role, remove. |
| `GET` | `{P}/board/` | Tickets grouped by status. |
| `GET` | `{P}/backlog/` | Tickets that are not in a sprint. |

### Tickets and labels

| Method | Path | What it does |
|---|---|---|
| `GET` `POST` | `{P}/tickets/` | List, create. |
| `GET` `PATCH` `DELETE` | `{P}/tickets/<ticket_id>/` | Read, update, delete. |
| `GET` `POST` | `{P}/labels/` | List, create labels. |
| `GET` `PATCH` `DELETE` | `{P}/labels/<label_id>/` | Read, update, delete a label. |
| `GET` `POST` | `{P}/tickets/<ticket_id>/labels/` | Labels on a ticket, apply one. |
| `DELETE` | `{P}/tickets/<ticket_id>/labels/<label_id>/` | Remove a label from a ticket. |

### Sprints

| Method | Path | What it does |
|---|---|---|
| `GET` `POST` | `{P}/sprints/` | List, create. |
| `GET` `PATCH` `DELETE` | `{P}/sprints/<sprint_id>/` | Read, update, delete. |
| `POST` | `{P}/sprints/<sprint_id>/start/` | Start the sprint. |
| `POST` | `{P}/sprints/<sprint_id>/complete/` | Complete the sprint. |
| `GET` `POST` | `{P}/sprints/<sprint_id>/tickets/` | List tickets, add a ticket. |
| `DELETE` | `{P}/sprints/<sprint_id>/tickets/<ticket_id>/` | Remove a ticket from the sprint. |

### Comments

Path: `{P}/tickets/<ticket_id>/comments/`

| Method | Path | What it does |
|---|---|---|
| `GET` `POST` | `/` | List, add a comment. |
| `PATCH` | `/<comment_id>/` | Edit your own comment. |
| `DELETE` | `/<comment_id>/` | Delete your own comment. Project leads can delete any. |

### Internal (`X-Service-Key`)

For other services only.

| Method | Path | What it does |
|---|---|---|
| `GET` | `/api/internal/teams/<team_id>/members/<user_id>/` | Is this user on the team? What role? |
| `GET` | `/api/internal/teams/<team_id>/projects/<project_id>/` | Does this project belong to this team? |
| `GET` | `/api/internal/projects/<project_id>/members/<user_id>/` | What is this user's project role? |
| `GET` | `/api/internal/projects/<project_id>/tickets/<key>/` | Find a ticket by key, like `DEV-12`. |

---

## Comments: files and mentions

**Files.** The file is stored in devboard-attachments. The comment keeps only the file ids. When you read a comment, work asks devboard-attachments for download links. A list of comments makes one call for the whole page. If devboard-attachments is down, comments still load, with an empty `attachments` list. Deleting a comment sends its attachment ids along with the `comment.deleted` event, so devboard-attachments can delete the files too instead of leaving them orphaned.

**Mentions.** Write `@username` in a comment. Work looks the name up in devboard-core and saves the user ids. These mentions are skipped, with no error:

- names that do not exist
- the author mentioning themselves
- users who are not on the project

When you edit a comment, the list is rebuilt. Only **new** mentions send a notification.

---

## Events

Work never sends events straight to Redis. It uses an **outbox**, so an event is not lost if Redis is down.

1. The change and the event are saved in **one database transaction**.
2. The relay container (`python manage.py drain_outbox`) reads unsent events every 2 seconds.
3. It sends them to Redis (stream `devboard:events`) or to devboard-email.
4. A failed send retries with a growing delay (4s, doubling up to a 300s cap) instead of failing fast. Up to 150 attempts — roughly half a day — before the row is left as failed and needs a manual retry.
5. Every event sent to Redis carries the outbox row's own id (`outbox_id`). If the relay crashes after sending but before marking the row delivered, the row is sent again on the next poll — `outbox_id` lets readers (like devboard-analytics) tell that redelivery apart from a genuinely new event, so it isn't double-counted.

Events on the stream:

| Group | Events |
|---|---|
| Tickets | `ticket.created`, `ticket.updated`, `ticket.assigned`, `ticket.unassigned`, `ticket.status_changed`, `ticket.deleted` |
| Epics and sprints on tickets | `ticket.epic_linked`, `ticket.epic_unlinked`, `ticket.sprint_added`, `ticket.sprint_removed` |
| Labels | `label.applied`, `label.removed` |
| Sprints | `sprint.started`, `sprint.completed` |
| Comments | `comment.created`, `comment.updated`, `comment.deleted`, `comment.mentioned` |

Events with a `recipient_id` (assigned, status changed, comment created, mentioned) become in-app notifications in devboard-integrations. `ticket.updated` carries `field`, `from_value` and `to_value`.

---

## Settings

Copy `.env.example` to `.env`.

| Variable | What it is |
|---|---|
| `SECRET_KEY` `DEBUG` | Django basics. |
| `DB_NAME` `DB_USER` `DB_PASSWORD` | Database login. |
| `DB_HOST` `DB_PORT` | Database address. Docker overrides them. |
| `JWT_SECRET` | Same value as devboard-auth. |
| `INTERNAL_API_KEY` | Shared key for service-to-service calls. |
| `CORE_SERVICE_URL` | devboard-core. |
| `EMAIL_SERVICE_URL` | devboard-email. |
| `ATTACHMENTS_SERVICE_URL` | devboard-attachments. |
| `REDIS_URL` | In Docker: `redis://devboard-redis:6379/0`. |

```bash
python manage.py makemigrations
python manage.py migrate
```
