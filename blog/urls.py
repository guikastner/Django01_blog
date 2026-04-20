from django.urls import path

from .views import PostCreateView, PostDetailView, PostListView, PostUpdateView, upload_content_image


app_name = "blog"

urlpatterns = [
    path("", PostListView.as_view(), name="post_list"),
    path("categories/<slug:category_slug>/", PostListView.as_view(), name="category_post_list"),
    path("posts/content-image-upload/", upload_content_image, name="post_content_image_upload"),
    path("posts/new/", PostCreateView.as_view(), name="post_create"),
    path("posts/<slug:slug>/edit/", PostUpdateView.as_view(), name="post_update"),
    path("posts/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
]
