from django.urls import include, path

from tickets.views import BoardView

from .views import ProjectDetailView, ProjectListCreateView, ProjectMemberView

urlpatterns = [
    path('', ProjectListCreateView.as_view()),
    path('<uuid:project_id>/', ProjectDetailView.as_view()),
    path('<uuid:project_id>/members/', ProjectMemberView.as_view()),
    path('<uuid:project_id>/members/<uuid:user_id>/', ProjectMemberView.as_view()),
    path('<uuid:project_id>/tickets/', include('tickets.urls')),
    path('<uuid:project_id>/labels/', include('labels.urls')),
    path('<uuid:project_id>/sprints/', include('sprints.urls')),
    path('<uuid:project_id>/board/', BoardView.as_view())
]