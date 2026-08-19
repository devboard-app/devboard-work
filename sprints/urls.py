from django.urls import path

from .views import (
    SprintCompleteView,
    SprintDetailView,
    SprintListCreateView,
    SprintStartView,
    SprintTicketView,
)

urlpatterns = [
    path('', SprintListCreateView.as_view()),
    path('<uuid:sprint_id>/', SprintDetailView.as_view()),
    path('<uuid:sprint_id>/start/', SprintStartView.as_view()),
    path('<uuid:sprint_id>/complete/', SprintCompleteView.as_view()),
    path('<uuid:sprint_id>/tickets/', SprintTicketView.as_view()),
    path('<uuid:sprint_id>/tickets/<uuid:ticket_id>/', SprintTicketView.as_view()),
]