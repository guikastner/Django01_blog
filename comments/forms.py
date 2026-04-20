from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    field_classes = {
        "name": "mt-2 min-h-11 w-full rounded-md border border-smoke bg-white px-3 py-2 text-ink shadow-sm transition placeholder:text-ink/35 focus:border-clay focus:outline-none focus:ring-2 focus:ring-clay/25",
        "email": "mt-2 min-h-11 w-full rounded-md border border-smoke bg-white px-3 py-2 text-ink shadow-sm transition placeholder:text-ink/35 focus:border-clay focus:outline-none focus:ring-2 focus:ring-clay/25",
        "body": "mt-2 w-full rounded-md border border-smoke bg-white px-3 py-3 text-ink shadow-sm transition placeholder:text-ink/35 focus:border-clay focus:outline-none focus:ring-2 focus:ring-clay/25",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, css_class in self.field_classes.items():
            self.fields[name].widget.attrs["class"] = css_class

    class Meta:
        model = Comment
        fields = ["name", "email", "body"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "body": forms.Textarea(attrs={"rows": 5}),
        }
