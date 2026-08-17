from rest_framework.exceptions import PermissionDenied

from .models import ProjectMembership
from .repository import get_project_membership


async def require_project_role(user_id:str, project_id: str, *allowed_roles) -> ProjectMembership:
    membership = await get_project_membership(user_id, project_id)
    if membership is None or membership.role not in allowed_roles:
        raise PermissionDenied()
    return membership