import re

from django.db import IntegrityError
from rest_framework.exceptions import NotFound, ValidationError

from .models import Project, ProjectMembership
from .repository import (
    create_project,
    create_project_membership,
    get_project_by_id,
    get_project_membership,
    get_projects_by_team,
)
from .repository import (
    delete_project as del_project,
)
from .repository import (
    delete_project_membership as del_project_membership,
)


def validate_key(key: str) -> None:
    if not re.match(r'^[A-Z0-9]{2,10}$', key):
        raise ValidationError('Key must be 2-10 uppercase alphanumeric characters')

async def get_project_or_404(project_id: str) -> Project:
    project = await get_project_by_id(project_id)
    if project is None:
        raise NotFound('Project not found.')
    return project

async def list_team_projects(team_id: str) -> list[Project]:
    return await get_projects_by_team(team_id)

async def create_project_with_lead(name: str, key: str, description: str, team: str, creator_id: str) -> Project:
    validate_key(key)
    try:
        project = await create_project(name, key, description, team, creator_id)
    except IntegrityError:
        raise ValidationError('A project with this key already exists.')
    await create_project_membership(project, creator_id, ProjectMembership.Role.LEAD)
    return project

async def update_project(project: Project, data: dict) -> Project:
    if 'key' in data:
        validate_key(data['key'])
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
