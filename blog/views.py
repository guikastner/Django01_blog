from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from comments.forms import CommentForm

from .forms import PostForm
from .models import Category, Post


def post_is_public(post):
    return (
        post.status == Post.Status.PUBLISHED
        and post.published_at is not None
        and post.published_at <= timezone.now()
    )


def public_categories():
    return (
        Category.objects.filter(
            posts__status=Post.Status.PUBLISHED,
            posts__published_at__lte=timezone.now(),
        )
        .distinct()
        .order_by("name")
    )


def upload_content_image(request):
    if not request.user.is_authenticated:
        return redirect(f"/admin/login/?next={request.path}")

    if not (request.user.has_perm("blog.add_post") or request.user.has_perm("blog.change_post")):
        raise PermissionDenied

    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

    image = request.FILES.get("image")
    if image is None:
        return JsonResponse({"error": "No image file was uploaded."}, status=400)

    content_type = getattr(image, "content_type", "")
    if content_type not in settings.ALLOWED_COVER_IMAGE_TYPES:
        return JsonResponse({"error": "Only JPEG, PNG, and WebP images are allowed."}, status=400)

    if image.size > settings.MAX_COVER_IMAGE_SIZE:
        max_mb = settings.MAX_COVER_IMAGE_SIZE // (1024 * 1024)
        return JsonResponse({"error": f"Images must be smaller than {max_mb} MB."}, status=400)

    extension = Path(image.name).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        extension = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }[content_type]

    now = timezone.now()
    path_name = f"posts/content/{now:%Y/%m}/{uuid4().hex}{extension}"
    saved_path = default_storage.save(path_name, image)
    return JsonResponse({"url": default_storage.url(saved_path)})


class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.published.select_related("author").prefetch_related("categories")
        self.category = None
        category_slug = self.kwargs.get("category_slug")
        if category_slug:
            self.category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(categories=self.category).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = public_categories()
        context["current_category"] = self.category
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Post.published.select_related("author").prefetch_related("categories", "comments")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        context["approved_comments"] = self.object.comments.filter(is_approved=True)
        context["categories"] = public_categories()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.save()
            messages.success(request, "Your comment was submitted and is awaiting approval.")
            return redirect(self.object.get_absolute_url())

        context = self.get_context_data()
        context["comment_form"] = form
        return self.render_to_response(context)


class PostEditorMixin(LoginRequiredMixin, PermissionRequiredMixin):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"
    login_url = "/admin/login/"

    def get_queryset(self):
        return Post.objects.select_related("author").prefetch_related("categories")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = public_categories()
        context["object_is_public"] = bool(getattr(self, "object", None) and post_is_public(self.object))
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["content"].widget.attrs["data-upload-url"] = reverse("blog:post_content_image_upload")
        return form

    def get_success_url(self):
        post = self.object
        if post_is_public(post):
            return post.get_absolute_url()
        if not self.request.user.has_perm("blog.change_post"):
            return reverse_lazy("blog:post_list")
        return reverse_lazy("blog:post_update", kwargs={"slug": post.slug})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class PostCreateView(PostEditorMixin, CreateView):
    permission_required = "blog.add_post"
    success_message = "Post saved."

    def get_success_url(self):
        if (
            self.object.status == Post.Status.PUBLISHED
            and self.object.published_at is not None
            and self.object.published_at <= timezone.now()
        ):
            return self.object.get_absolute_url()
        return reverse_lazy("blog:post_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(PostEditorMixin, UpdateView):
    permission_required = "blog.change_post"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_message = "Post updated."
