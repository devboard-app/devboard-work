from .models import Team, TeamMembership


async def get_team_by_id(team_id: str)->Team | None:
    return await Team.objects.filter(id=team_id).afirst()

async def get_teams_by_user(user_id: str)-> list[TeamMembership]:
    return [m async for m in TeamMembership.objects.filter(user_id=user_id).select_related('team')]

async def create_team(name: str, description: str, owner_id: str) -> Team:
    return await Team.objects.acreate(name=name, description=description, owner_id=owner_id)

async def create_membership(team: Team, user_id: str, role: str) -> TeamMembership:
    return await TeamMembership.objects.acreate(team=team, user_id=user_id, role=role)

async def get_membership_by_user_and_team(user_id: str, team_id: str) -> TeamMembership | None:
    return await TeamMembership.objects.filter(user_id=user_id, team_id=team_id).afirst()

async def get_membership_by_team(team_id: str) -> list[TeamMembership]:
    return [m async for m in TeamMembership.objects.filter(team_id = team_id)]

async def delete_membership(membership: TeamMembership) -> None:
    await membership.adelete()

async def count_owners(team_id: str) -> int:
    return await TeamMembership.objects.filter(team_id=team_id,role='owner').acount()