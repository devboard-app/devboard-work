
from django.urls import include, path

from .views import (
    TeamDetailView,
    TeamListCreateView,
    TeamMemberDetailView,
    TeamMemberLeaveView,
    TeamMemberListAddView,
)

urlpatterns = [
    path('', TeamListCreateView.as_view(), name='team-list-create'),
    path('<uuid:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('<uuid:pk>/members/', TeamMemberListAddView.as_view(), name='team-member-list-add'),
    path('<uuid:pk>/members/me/', TeamMemberLeaveView.as_view(), name='team-member-leave'),
    path('<uuid:pk>/members/<uuid:user_id>/', TeamMemberDetailView.as_view(), name='team-member-detail'),
    path('<uuid:team_id>/projects/', include('projects.urls'))
]