
from django.urls import path

from .views import TicketDetailView, TicketListCreateView

urlpatterns = [
    path('', TicketListCreateView.as_view(), name='ticket-list-create'),
    path('<uuid:ticket_id>/', TicketDetailView.as_view(), name='ticket-get-update-delete')    
]