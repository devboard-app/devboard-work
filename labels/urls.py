from django.urls import path

from .views import LabelDetailView, LabelListCreateView

urlpatterns = [
    path('', LabelListCreateView.as_view(), name='label-list-create'),
    path('<uuid:label_id>/', LabelDetailView.as_view(), name='label-detail-view')
]