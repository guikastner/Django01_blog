from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    field_classes = {
        "body": "mt-2 w-full rounded-2xl border border-line bg-white px-4 py-3 text-ink shadow-sm transition placeholder:text-muted/50 focus:border-brand focus:outline-none focus:ring-4 focus:ring-brand/20",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, css_class in self.field_classes.items():
            self.fields[name].widget.attrs["class"] = css_class

    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),
        }
