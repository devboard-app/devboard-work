from django.urls import path

from .views import TicketLabelView

urlpatterns = [
    path('', TicketLabelView.as_view()),
    path('<uuid:label_id>/', TicketLabelView.as_view()),
]