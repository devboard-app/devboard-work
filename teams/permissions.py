from rest_framework.exceptions import PermissionDenied

from .repository import get_membership_by_user_and_team


async def require_team_role(user_id: str, team_id: str, *allowed_roles: str):
    membership = await get_membership_by_user_and_team(user_id, team_id)
    if membership is None or membership.role not in allowed_roles:
        raise PermissionDenied()
    return membership

def can_assign_role(requester_role: str, target_role: str) -> bool:
    hierarchy = ['owner', 'admin', 'member', 'viewer']
    if requester_role not in hierarchy or target_role not in hierarchy:
        return False
    return hierarchy.index(requester_role) < hierarchy.index(target_role)