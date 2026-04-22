from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from comments.forms import CommentForm
from comments.models import Comment
from accounts.models import UserProfile

from .forms import CategoryForm, PostForm
from .media import save_editor_image, validate_editor_image
from .models import Category, Post


class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return Post.published.select_related("author")


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Post.published.select_related("author").prefetch_related("comments")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        context["approved_comments"] = self.object.comments.filter(is_approved=True)
        if self.request.user.is_authenticated:
            context["comment_profile"] = UserProfile.for_user(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        self.object = self.get_object()
        profile = UserProfile.for_user(request.user)
        if profile.is_comment_banned:
            messages.error(request, "Your account is not allowed to submit comments.")
            return redirect(self.object.get_absolute_url())

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.user = request.user
            comment.name = request.user.get_full_name() or request.user.username
            comment.email = request.user.email
            comment.save()
            messages.success(request, "Your comment was submitted and is awaiting approval.")
            return redirect(self.object.get_absolute_url())

        context = self.get_context_data()
        context["comment_form"] = form
        return self.render_to_response(context)


class PostFormMixin(LoginRequiredMixin, PermissionRequiredMixin):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    submit_icon = "save-post"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content_upload_url"] = reverse("blog:post_content_upload")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = self.form_title
        context["submit_label"] = self.submit_label
        context["submit_icon"] = self.submit_icon
        context["can_view_post"] = bool(getattr(self, "object", None) and self.object.is_public())
        return context

    def get_success_url(self):
        if self.object.is_public():
            return self.object.get_absolute_url()
        if self.request.user.has_perm("blog.change_post"):
            return reverse("blog:post_update", kwargs={"slug": self.object.slug})
        return reverse("blog:post_list")


class PostCreateView(PostFormMixin, CreateView):
    permission_required = "blog.add_post"
    form_title = "Create post"
    submit_label = "Save post"

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "Post saved.")
        return super().form_valid(form)


class PostUpdateView(PostFormMixin, UpdateView):
    permission_required = "blog.change_post"
    form_title = "Edit post"
    submit_label = "Update post"
    submit_icon = "update-post"

    def get_queryset(self):
        return Post.objects.select_related("author")

    def form_valid(self, form):
        messages.success(self.request, "Post updated.")
        return super().form_valid(form)


class PostContentUploadView(LoginRequiredMixin, View):
    def has_upload_permission(self):
        user = self.request.user
        return user.has_perm("blog.add_post") or user.has_perm("blog.change_post")

    def post(self, request, *args, **kwargs):
        if not self.has_upload_permission():
            return JsonResponse({"error": "You do not have permission to upload media."}, status=403)

        image = request.FILES.get("image")
        if image is None:
            return JsonResponse({"error": "No image file was uploaded."}, status=400)

        error = validate_editor_image(image)
        if error:
            return JsonResponse({"error": error}, status=400)

        return JsonResponse({"url": save_editor_image(image)})


class DashboardPostListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Post
    template_name = "blog/dashboard/post_list.html"
    context_object_name = "posts"
    permission_required = "blog.view_post"
    paginate_by = 20

    def get_queryset(self):
        return (
            Post.objects.select_related("author")
            .prefetch_related("categories")
            .annotate(
                total_comments=Count("comments", distinct=True),
                pending_comments=Count("comments", filter=Q(comments__is_approved=False), distinct=True),
            )
            .order_by("-published_at", "-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_comment_count"] = Comment.objects.filter(is_approved=False).count()
        context["category_count"] = Category.objects.count()
        return context


class DashboardPostDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/dashboard/post_confirm_delete.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    permission_required = "blog.delete_post"

    def get_queryset(self):
        return Post.objects.select_related("author")

    def get_success_url(self):
        return reverse("blog:dashboard_posts")

    def form_valid(self, form):
        messages.success(self.request, "Post deleted.")
        return super().form_valid(form)


class DashboardCategoryView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "blog.add_category"
    template_name = "blog/dashboard/categories.html"
    form_class = CategoryForm

    def get(self, request, *args, **kwargs):
        return self.render(request, self.form_class())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added.")
            return redirect("blog:dashboard_categories")
        return self.render(request, form)

    def render(self, request, form):
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "categories": Category.objects.annotate(post_count=Count("posts")),
            },
        )


class DashboardCommentModerationView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Comment
    template_name = "blog/dashboard/comments.html"
    context_object_name = "comments"
    permission_required = "comments.change_comment"
    paginate_by = 25

    def get_queryset(self):
        queryset = Comment.objects.select_related("post").order_by("is_approved", "-created_at")
        if self.request.GET.get("status") == "approved":
            return queryset.filter(is_approved=True)
        if self.request.GET.get("status") == "pending":
            return queryset.filter(is_approved=False)
        return queryset

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=request.POST.get("comment_id"))
        action = request.POST.get("action")

        if action == "approve":
            comment.is_approved = True
            comment.save(update_fields=["is_approved", "updated_at"])
            messages.success(request, "Comment approved.")
        elif action == "reject":
            comment.is_approved = False
            comment.save(update_fields=["is_approved", "updated_at"])
            messages.success(request, "Comment moved back to pending.")
        elif action == "delete":
            if not request.user.has_perm("comments.delete_comment"):
                raise PermissionDenied
            comment.delete()
            messages.success(request, "Comment deleted.")
        else:
            messages.error(request, "Unknown moderation action.")

        return redirect(request.get_full_path())


class DashboardUserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = UserProfile
    template_name = "blog/dashboard/users.html"
    context_object_name = "profiles"
    permission_required = "accounts.view_userprofile"
    paginate_by = 25

    def get_queryset(self):
        queryset = (
            UserProfile.objects.select_related("user", "comment_banned_by")
            .annotate(
                total_comments=Count("user__comments", distinct=True),
                approved_comments=Count("user__comments", filter=Q(user__comments__is_approved=True), distinct=True),
            )
            .order_by("user__username")
        )
        username = self.request.GET.get("username", "").strip()
        email = self.request.GET.get("email", "").strip()
        if username:
            queryset = queryset.filter(user__username__icontains=username)
        if email:
            queryset = queryset.filter(user__email__icontains=email)
        return queryset

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("accounts.change_userprofile"):
            raise PermissionDenied

        profile = get_object_or_404(UserProfile.objects.select_related("user"), pk=request.POST.get("profile_id"))
        action = request.POST.get("action")

        if action == "ban_comments":
            profile.ban_from_comments(request.user, request.POST.get("comment_ban_reason", ""))
            messages.success(request, f"{profile.user.username} can no longer submit comments.")
        elif action == "allow_comments":
            profile.allow_comments()
            messages.success(request, f"{profile.user.username} can submit comments again.")
        else:
            messages.error(request, "Unknown user action.")

        return redirect(request.get_full_path())
