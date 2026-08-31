from django.urls import path

from .views import CommentDetailView, CommentListCreateView

urlpatterns = [
    path('', CommentListCreateView.as_view(), name='comment-list-create'),
    path('<uuid:comment_id>/', CommentDetailView.as_view(), name='comment-detail'),
]