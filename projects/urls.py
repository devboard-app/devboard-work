from django.urls import path

from .views import ProjectDetailView, ProjectListCreateView, ProjectMemberView

urlpatterns = [
    path('', ProjectListCreateView.as_view()),
    path('<uuid:project_id>/', ProjectDetailView.as_view()),
    path('<uuid:project_id>/members/', ProjectMemberView.as_view()),
    path('<uuid:project_id>/members/<uuid:user_id>/', ProjectMemberView.as_view())
]