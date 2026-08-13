
from django.urls import path

from .views import (
    TeamDetailView,
    TeamListCreateView,
    TeamMemberDetailView,
    TeamMemberLeaveView,
    TeamMemberListInviteView,
)

urlpatterns = [
    path('', TeamListCreateView.as_view(), name='team-list-create'),
    path('<uuid:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('<uuid:pk>/members/', TeamMemberListInviteView.as_view(), name='team-member-list-invite'),
    path('<uuid:pk>/members/me/', TeamMemberLeaveView.as_view(), name='team-member-leave'),
    path('<uuid:pk>/members/<uuid:user_id>/', TeamMemberDetailView.as_view(), name='team-member-detail'),
]