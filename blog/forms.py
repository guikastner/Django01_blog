from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    field_classes = {
        "title": "mt-2 min-h-11 w-full rounded-2xl border border-line bg-white px-4 py-3 text-ink shadow-sm transition placeholder:text-muted/50 focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/20",
        "slug": "mt-2 min-h-11 w-full rounded-2xl border border-line bg-white px-4 py-3 text-ink shadow-sm transition placeholder:text-muted/50 focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/20",
        "excerpt": "mt-2 w-full rounded-2xl border border-line bg-white px-4 py-3 text-ink shadow-sm transition placeholder:text-muted/50 focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/20",
        "content": "mt-2 min-h-[22rem] w-full rounded-2xl border border-line bg-white px-4 py-3 font-serif text-lg leading-8 text-ink shadow-sm transition placeholder:text-muted/50 focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/20",
        "cover_image": "mt-2 block w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-muted shadow-sm file:mr-4 file:rounded-full file:border-0 file:bg-accent file:px-4 file:py-2 file:text-sm file:font-bold file:text-white hover:file:bg-brand focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/20",
        "categories": "mt-2 min-h-32 w-full rounded-2xl border border-line bg-white px-4 py-3 text-ink shadow-sm transition focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/20",
        "status": "mt-2 min-h-11 w-full rounded-2xl border border-line bg-white px-4 py-3 text-ink shadow-sm transition focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/20",
        "published_at": "mt-2 min-h-11 w-full rounded-2xl border border-line bg-white px-4 py-3 text-ink shadow-sm transition focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/20",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, css_class in self.field_classes.items():
            self.fields[name].widget.attrs["class"] = css_class

    class Meta:
        model = Post
        fields = ["title", "slug", "excerpt", "content", "cover_image", "categories", "status", "published_at"]
        widgets = {
            "excerpt": forms.Textarea(attrs={"rows": 4}),
            "content": forms.Textarea(),
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }
