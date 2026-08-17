from rest_framework.exceptions import PermissionDenied

from .models import TeamMembership
from .repository import get_membership_by_user_and_team

Role = TeamMembership.Role

async def require_team_role(user_id: str, team_id: str, *allowed_roles: str):
    membership = await get_membership_by_user_and_team(user_id, team_id)
    if membership is None or membership.role not in allowed_roles:
        raise PermissionDenied()
    return membership

def can_assign_role(requester_role: str, target_role: str) -> bool:
    hierarchy = [Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER]
    if requester_role not in hierarchy or target_role not in hierarchy:
        return False
    return hierarchy.index(Role(requester_role)) < hierarchy.index(Role(target_role))