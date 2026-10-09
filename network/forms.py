from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Comment, Post, Profile

User = get_user_model()
MAX_IMAGE_MB = 5


def _check_image_size(image):
    if image and hasattr(image, "size") and image.size > MAX_IMAGE_MB * 1024 * 1024:
        raise forms.ValidationError(f"Images must be {MAX_IMAGE_MB} MB or smaller.")
    return image


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("content", "image")
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3, "maxlength": 500, "placeholder": "What's happening?"}),
            "image": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean_image(self):
        return _check_image_size(self.cleaned_data.get("image"))

    def clean(self):
        data = super().clean()
        content = (data.get("content") or "").strip()
        data["content"] = content
        if not content and not data.get("image") and not self.errors:
            raise forms.ValidationError("Write something or attach an image to post.")
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("content",)
        widgets = {"content": forms.TextInput(attrs={"maxlength": 300, "placeholder": "Write a comment"})}

    def clean_content(self):
        content = self.cleaned_data["content"].strip()
        if not content:
            raise forms.ValidationError("Comment can't be empty.")
        return content


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("bio", "location", "website", "avatar")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3, "maxlength": 280}),
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean_avatar(self):
        return _check_image_size(self.cleaned_data.get("avatar"))
