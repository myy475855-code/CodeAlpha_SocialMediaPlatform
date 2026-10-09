from django.contrib import admin

from .models import Comment, Follow, Like, Post, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "website")
    search_fields = ("user__username", "bio")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "short", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "author__username")

    @admin.display(description="Content")
    def short(self, obj):
        return obj.content[:60]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "created_at")


admin.site.register(Follow)
admin.site.register(Like)
