from django.urls import path

from .views import PostContentUploadView, PostCreateView, PostDetailView, PostListView, PostUpdateView


app_name = "blog"

urlpatterns = [
    path("", PostListView.as_view(), name="post_list"),
    path("posts/new/", PostCreateView.as_view(), name="post_create"),
    path("posts/editor/upload-media/", PostContentUploadView.as_view(), name="post_content_upload"),
    path("posts/<slug:slug>/edit/", PostUpdateView.as_view(), name="post_update"),
    path("posts/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
]
