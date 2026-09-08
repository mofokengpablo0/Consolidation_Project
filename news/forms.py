from django import forms
from .models import Article


class ArticleForm(forms.ModelForm):
    """Form for creating and editing articles."""

    class Meta:
        model = Article
        fields = ["title", "content", "summary", "publisher", "image"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 15}),
            "summary": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters.")
        return title

    def clean_content(self):
        content = self.cleaned_data.get("content", "")
        if len(content) < 20:
            raise forms.ValidationError("Content must be at least 20 characters.")
        return content
