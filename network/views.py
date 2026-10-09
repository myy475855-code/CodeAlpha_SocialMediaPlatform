from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm, ProfileForm, RegisterForm
from .models import Comment, Follow, Like, Post, Profile

User = get_user_model()
PAGE_SIZE = 10


# ---------------------------------------------------------------- helpers

def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _safe_next(request, fallback):
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
        return target
    return fallback


def _with_counts(qs):
    return qs.select_related("author", "author__profile").annotate(
        like_count=Count("likes", distinct=True),
        comment_count=Count("comments", distinct=True),
    )


def _mark_liked(posts, user):
    """Return posts as a list, each with `liked_by_me` set."""
    posts = list(posts)
    liked = set()
    if user.is_authenticated and posts:
        liked = set(Like.objects.filter(user=user, post__in=posts).values_list("post_id", flat=True))
    for post in posts:
        post.liked_by_me = post.pk in liked
    return posts


def _following_ids(user):
    if not user.is_authenticated:
        return set()
    return set(user.following_links.values_list("following_id", flat=True))


# ---------------------------------------------------------------- auth

def register(request):
    if request.user.is_authenticated:
        return redirect("feed")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.username}! Follow a few people to fill your feed.")
        return redirect("feed")
    return render(request, "registration/register.html", {"form": form})


# ---------------------------------------------------------------- feed & posts

def feed(request):
    tab = request.GET.get("tab", "following")
    qs = _with_counts(Post.objects.all())
    if request.user.is_authenticated and tab != "everyone":
        tab = "following"
        ids = list(_following_ids(request.user)) + [request.user.pk]
        qs = qs.filter(author_id__in=ids)
    else:
        tab = "everyone"
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "network/feed.html", {
        "page": page,
        "posts": _mark_liked(page.object_list, request.user),
        "tab": tab,
        "form": PostForm(),
    })


@login_required
@require_POST
def post_create(request):
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, "Posted.")
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect("feed")


def post_detail(request, pk):
    post = get_object_or_404(_with_counts(Post.objects.all()), pk=pk)
    post = _mark_liked([post], request.user)[0]
    comments = post.comments.select_related("author", "author__profile")
    return render(request, "network/post_detail.html", {
        "post": post,
        "comments": comments,
        "form": CommentForm(),
    })


@login_required
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    post.delete()
    messages.success(request, "Post deleted.")
    return redirect(_safe_next(request, "feed"))


@login_required
@require_POST
def like_toggle(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
    if _is_ajax(request):
        return JsonResponse({"liked": created, "count": post.likes.count()})
    return redirect(_safe_next(request, post.get_absolute_url()))


@login_required
@require_POST
def comment_add(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect(f"{post.get_absolute_url()}#comments")


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment.objects.select_related("post"), pk=pk)
    if request.user not in (comment.author, comment.post.author):
        raise PermissionDenied
    post_url = comment.post.get_absolute_url()
    comment.delete()
    return redirect(f"{post_url}#comments")


# ---------------------------------------------------------------- profiles & follows

def profile(request, username):
    owner = get_object_or_404(User.objects.select_related("profile"), username=username)
    qs = _with_counts(Post.objects.filter(author=owner))
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    is_following = (
        request.user.is_authenticated
        and Follow.objects.filter(follower=request.user, following=owner).exists()
    )
    return render(request, "network/profile.html", {
        "owner": owner,
        "page": page,
        "posts": _mark_liked(page.object_list, request.user),
        "post_count": owner.posts.count(),
        "followers_count": owner.follower_links.count(),
        "following_count": owner.following_links.count(),
        "is_following": is_following,
    })


@login_required
def profile_edit(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("profile", username=request.user.username)
    return render(request, "network/profile_edit.html", {"form": form})


@login_required
@require_POST
def follow_toggle(request, username):
    target = get_object_or_404(User, username=username)
    fallback = target.profile.get_absolute_url() if hasattr(target, "profile") else "feed"
    if target == request.user:
        messages.error(request, "You can't follow yourself.")
        return redirect(_safe_next(request, fallback))
    link, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        link.delete()
    if _is_ajax(request):
        return JsonResponse({"following": created, "followers": target.follower_links.count()})
    return redirect(_safe_next(request, fallback))


def _user_list(request, owner, title, people):
    return render(request, "network/user_list.html", {
        "owner": owner,
        "title": title,
        "people": people.select_related("profile").order_by("username"),
        "my_following_ids": _following_ids(request.user),
    })


def followers(request, username):
    owner = get_object_or_404(User, username=username)
    return _user_list(request, owner, "Followers", User.objects.filter(following_links__following=owner))


def following(request, username):
    owner = get_object_or_404(User, username=username)
    return _user_list(request, owner, "Following", User.objects.filter(follower_links__follower=owner))


# ---------------------------------------------------------------- search

def search(request):
    q = request.GET.get("q", "").strip()
    people, posts = [], []
    if q:
        people = (
            User.objects.filter(Q(username__icontains=q) | Q(profile__bio__icontains=q))
            .select_related("profile")
            .order_by("username")[:20]
        )
        posts = _mark_liked(_with_counts(Post.objects.filter(content__icontains=q))[:20], request.user)
    return render(request, "network/search.html", {
        "q": q,
        "people": people,
        "posts": posts,
        "my_following_ids": _following_ids(request.user),
    })
