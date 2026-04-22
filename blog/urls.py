from django.urls import path

from .views import (
    DashboardCategoryView,
    DashboardCommentModerationView,
    DashboardPostDeleteView,
    DashboardPostListView,
    PostContentUploadView,
    PostCreateView,
    PostDetailView,
    PostListView,
    PostUpdateView,
)


app_name = "blog"

urlpatterns = [
    path("", PostListView.as_view(), name="post_list"),
    path("dashboard/", DashboardPostListView.as_view(), name="dashboard_posts"),
    path("dashboard/categories/", DashboardCategoryView.as_view(), name="dashboard_categories"),
    path("dashboard/comments/", DashboardCommentModerationView.as_view(), name="dashboard_comments"),
    path("dashboard/posts/<slug:slug>/delete/", DashboardPostDeleteView.as_view(), name="dashboard_post_delete"),
    path("posts/new/", PostCreateView.as_view(), name="post_create"),
    path("posts/editor/upload-media/", PostContentUploadView.as_view(), name="post_content_upload"),
    path("posts/<slug:slug>/edit/", PostUpdateView.as_view(), name="post_update"),
    path("posts/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
]
