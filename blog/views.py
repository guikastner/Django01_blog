from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from comments.forms import CommentForm

from .forms import PostForm
from .media import save_editor_image, validate_editor_image
from .models import Post


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
