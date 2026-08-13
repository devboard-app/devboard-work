
from django.urls import path

from .views import TeamDetailView, TeamListCreateView

urlpatterns = [
    path('', TeamListCreateView.as_view(), name='team-list-create'),
    path('<uuid:pk>/', TeamDetailView.as_view(), name='team-detail'),
]