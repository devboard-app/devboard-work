
from django.db import IntegrityError
from rest_framework.exceptions import NotFound, ValidationError

from teams.models import Team

from .models import Project, ProjectMembership
from .repository import (
    create_project,
    create_project_membership,
    get_memberships_by_project_page,
    get_project_by_id,
    get_project_membership,
    get_projects_by_team,
    update_project_membership,
)
from .repository import (
    delete_project as del_project,
)
from .repository import (
    delete_project_membership as del_project_membership,
)


async def get_project_or_404(project_id: str, team_id: str) -> Project:
    project = await get_project_by_id(project_id, team_id)
    if project is None:
        raise NotFound('Project not found.')
    return project

async def get_project_member_or_404(user_id: str, project_id: str) -> ProjectMembership:
    membership = await get_project_membership(user_id, project_id)
    if membership is None:
        raise NotFound('Member not found in this project.')
    return membership

async def list_team_projects(team_id: str, limit: int, offset: int) -> tuple[list[Project], int]:
    return await get_projects_by_team(team_id, limit, offset)

async def create_project_with_lead(data: dict, team: Team, creator_id: str) -> Project:
    try:
        project = await create_project(data['name'], data['key'], data['description'], team, creator_id)
    except IntegrityError:
        raise ValidationError('A project with this key already exists.')
    
    try:
        await create_project_membership(project, creator_id, ProjectMembership.Role.LEAD)
    except Exception:  # noqa: BLE001
        await delete_project(project)
        raise ValidationError("Something went wrong, please try again.")
    
    return project

async def update_project(project: Project, data: dict) -> Project:
    for key, value in data.items():
        setattr(project, key, value)
    try:
        await project.asave()
    except IntegrityError:
        raise ValidationError('A project with this key already exists.')
    return project

async def delete_project(project: Project) -> None:
    await del_project(project)

async def add_project_member(project: Project, user_id: str, role: str) -> ProjectMembership:
    membership = await get_project_membership(user_id, str(project.id))
    if membership is not None:
        raise ValidationError('User is already a member.')
    
    return await create_project_membership(project, user_id, role)

async def remove_project_member(project_id: str, user_id: str) -> None:
    membership = await get_project_membership(project_id=project_id, user_id=user_id)
    if membership is None:
        raise NotFound('Member not found in this project.')
    await del_project_membership(membership)

async def list_project_members(project_id: str, limit: int, offset: int) -> tuple[list[ProjectMembership], int]:
    return await get_memberships_by_project_page(project_id, limit, offset)

async def update_project_member(membership: ProjectMembership, role: str) -> ProjectMembership:
    return await update_project_membership(membership, role)