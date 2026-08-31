
from django.urls import include, path

from .views import TicketDetailView, TicketListCreateView

urlpatterns = [
    path('', TicketListCreateView.as_view(), name='ticket-list-create'),
    path('<uuid:ticket_id>/', TicketDetailView.as_view(), name='ticket-get-update-delete'),
    path('<uuid:ticket_id>/labels/', include('labels.ticket_urls')),
    path('<uuid:ticket_id>/comments/', include('comments.ticket_urls')),
]