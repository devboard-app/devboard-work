from django.urls import path

from .views import ProjectDetailView, ProjectListCreateView

urlpatterns = [
    path('', ProjectListCreateView.as_view()),
    path('<uuid:project_id>/', ProjectDetailView.as_view()),
]