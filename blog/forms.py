from django import forms

from .models import Category, Post


INPUT_CLASS = (
    "mt-2 block min-h-12 w-full rounded-[1.1rem] border border-line bg-white/95 px-4 py-3 "
    "text-base text-ink shadow-sm outline-none transition focus:border-brand "
    "focus:ring-4 focus:ring-brand/20"
)
TEXTAREA_CLASS = (
    "mt-2 block w-full rounded-[1.1rem] border border-line bg-white/95 px-4 py-3 "
    "text-base text-ink shadow-sm outline-none transition focus:border-brand "
    "focus:ring-4 focus:ring-brand/20"
)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("title", "slug", "excerpt", "content", "cover_image", "categories", "status", "published_at")
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "slug": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "excerpt": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 3}),
            "content": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 14}),
            "cover_image": forms.ClearableFileInput(
                attrs={
                    "class": (
                        "mt-2 block w-full rounded-[1.1rem] border border-dashed border-line bg-white/80 "
                        "px-4 py-3 text-sm text-muted file:mr-4 file:rounded-full file:border-0 "
                        "file:bg-accent file:px-4 file:py-2 file:text-sm file:font-bold file:text-white"
                    )
                }
            ),
            "status": forms.Select(attrs={"class": INPUT_CLASS}),
            "categories": forms.CheckboxSelectMultiple(),
            "published_at": forms.DateTimeInput(
                attrs={"class": INPUT_CLASS, "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        content_upload_url = kwargs.pop("content_upload_url", "")
        super().__init__(*args, **kwargs)
        self.fields["content"].widget.attrs["data-upload-url"] = content_upload_url
        self.fields["published_at"].input_formats = ["%Y-%m-%dT%H:%M"]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "slug", "description")
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "slug": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "description": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 4}),
        }
