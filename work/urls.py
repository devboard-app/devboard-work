"""
URL configuration for work project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from teams.internal_views import InternalTeamCheckView
from tickets.internal_views import InternalTicketByKeyView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/teams/', include('teams.urls')),
    path('api/internal/teams/<uuid:team_id>/members/<uuid:user_id>/', InternalTeamCheckView.as_view(), name='internal-team-check'),
    path('api/internal/projects/<uuid:project_id>/tickets/<str:key>/', InternalTicketByKeyView.as_view(), name='internal-ticket-by-key'),
]
