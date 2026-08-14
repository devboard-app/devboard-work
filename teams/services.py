from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from .infrastructure import get_user_id_by_email
from .models import Team, TeamMembership
from .permissions import can_assign_role
from .repository import (
    create_membership,
    create_team,
    delete_membership,
    get_membership_by_user_and_team,
    get_team_by_id,
    get_teams_by_user,
)


async def get_team_or_404(pk: str) -> Team:
    team = await get_team_by_id(pk)
    if team is None:
        raise NotFound('Team not found.')
    return team

async def list_my_teams(user_id: str):
    memberships = await get_teams_by_user(user_id)
    return [m.team for m in memberships]

async def create_team_with_owner(name: str, description: str, owner_id: str):
    team = await create_team(name, description, owner_id)
    await create_membership(team, owner_id, TeamMembership.Role.OWNER)
    return team    

async def invite_member(team: Team, requester_role: str, email: str, target_role: str) -> TeamMembership:
    if not can_assign_role(requester_role, target_role):
        raise PermissionDenied('You cannot assign this role.')
    user_id = await get_user_id_by_email(email)
    if user_id is None:
        raise NotFound('User not found.')
    existing = await get_membership_by_user_and_team(str(user_id), str(team.id))
    if existing is not None:
        raise ValidationError('User is already a member.')
    return await create_membership(team, user_id, target_role)

async def remove_member(team_id: str, user_id: str) -> None:
    target_membership = await get_membership_by_user_and_team(str(user_id), str(team_id))
    if target_membership is None:
        raise NotFound('User not found')
    if target_membership.role == 'owner':
        raise PermissionDenied('Cannot remove a team owner.')
    await delete_membership(target_membership)

async def change_member_role(team_id: str, user_id: str, requester_role: str, target_role: str) -> TeamMembership:
    target_membership = await get_membership_by_user_and_team(str(user_id), str(team_id))
    if target_membership is None:
        raise NotFound('User not found.')
    if not can_assign_role(requester_role, target_role):
        raise PermissionDenied('You cannot assign this role.')
    if target_membership.role == 'owner':
        raise PermissionDenied('You cannot demote the owner.')
    target_membership.role = target_role
    await target_membership.asave()
    return target_membership

async def leave_team(team_id: str, user_id: str) -> None:
    membership = await get_membership_by_user_and_team(user_id, team_id)
    if membership is None:
        raise NotFound('You are not a member of this team.')
    if membership.role == 'owner':
        raise PermissionDenied('Cannot leave team if you are the owner.')
    await delete_membership(membership)
