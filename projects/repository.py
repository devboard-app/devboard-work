from teams.models import Team

from .models import Project, ProjectMembership


async def get_project_by_id(project_id: str) -> Project | None:
    return await Project.objects.filter(id=project_id).afirst()

async def get_projects_by_team(team_id: str) -> list[Project]:
    return [m async for m in  Project.objects.filter(team=team_id).select_related('team')]


async def create_project(name: str, key: str, description: str, team: Team, created_by: str) -> Project:
    return await Project.objects.acreate(name=name, key=key, description=description, team=team, created_by=created_by)

async def delete_project(project: Project)-> None:
    await project.adelete()

async def create_project_membership(project: Project, user_id: str, role: str) -> ProjectMembership:
    return await ProjectMembership.objects.acreate(project=project, user_id=user_id, role=role)

async def get_project_membership(user_id: str, project_id: str) -> ProjectMembership | None:
    return await ProjectMembership.objects.filter(user_id=user_id, project=project_id).afirst()

async def get_memberships_by_project(project_id: str) -> list[ProjectMembership]:
    return [m async for m in ProjectMembership.objects.filter(project=project_id)]

async def delete_project_membership(membership: ProjectMembership) -> None:
    await membership.adelete()