from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Follow, Like, Post

User = get_user_model()


class SocialTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", "a@example.com", "pass12345!")
        self.bob = User.objects.create_user("bob", "b@example.com", "pass12345!")

    def test_register_creates_user_and_profile(self):
        resp = self.client.post(reverse("register"), {
            "username": "carol", "email": "c@example.com",
            "password1": "Str0ng-pass-99", "password2": "Str0ng-pass-99",
        })
        self.assertRedirects(resp, reverse("feed"))
        self.assertTrue(User.objects.get(username="carol").profile)

    def test_login_required_for_posting(self):
        resp = self.client.post(reverse("post_create"), {"content": "hi"})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])
        self.assertEqual(Post.objects.count(), 0)

    def test_create_post_and_empty_post_rejected(self):
        self.client.force_login(self.alice)
        self.client.post(reverse("post_create"), {"content": "hello world"})
        self.client.post(reverse("post_create"), {"content": "   "})
        self.assertEqual(Post.objects.count(), 1)

    def test_like_toggle(self):
        post = Post.objects.create(author=self.bob, content="x")
        self.client.force_login(self.alice)
        r1 = self.client.post(reverse("like_toggle", args=[post.pk]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r1.json(), {"liked": True, "count": 1})
        r2 = self.client.post(reverse("like_toggle", args=[post.pk]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r2.json(), {"liked": False, "count": 0})
        self.assertEqual(Like.objects.count(), 0)

    def test_follow_toggle_and_self_follow_blocked(self):
        self.client.force_login(self.alice)
        r = self.client.post(reverse("follow_toggle", args=["bob"]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r.json(), {"following": True, "followers": 1})
        self.client.post(reverse("follow_toggle", args=["alice"]))
        self.assertFalse(Follow.objects.filter(follower=self.alice, following=self.alice).exists())
        r = self.client.post(reverse("follow_toggle", args=["bob"]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r.json(), {"following": False, "followers": 0})

    def test_following_feed_only_shows_followed_and_own(self):
        carol = User.objects.create_user("carol", "c@example.com", "pass12345!")
        Post.objects.create(author=self.alice, content="mine")
        Post.objects.create(author=self.bob, content="bobs")
        Post.objects.create(author=carol, content="carols")
        Follow.objects.create(follower=self.alice, following=self.bob)
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("feed"))
        self.assertContains(resp, "mine")
        self.assertContains(resp, "bobs")
        self.assertNotContains(resp, "carols")
        resp = self.client.get(reverse("feed") + "?tab=everyone")
        self.assertContains(resp, "carols")

    def test_comments_and_permissions(self):
        post = Post.objects.create(author=self.bob, content="x")
        self.client.force_login(self.alice)
        self.client.post(reverse("comment_add", args=[post.pk]), {"content": "nice"})
        comment = Comment.objects.get()
        self.assertEqual(comment.author, self.alice)
        # a third user cannot delete it
        carol = User.objects.create_user("carol", "c@example.com", "pass12345!")
        self.client.force_login(carol)
        self.assertEqual(self.client.post(reverse("comment_delete", args=[comment.pk])).status_code, 403)
        # the post owner can
        self.client.force_login(self.bob)
        self.client.post(reverse("comment_delete", args=[comment.pk]))
        self.assertEqual(Comment.objects.count(), 0)

    def test_only_author_can_delete_post(self):
        post = Post.objects.create(author=self.bob, content="x")
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(reverse("post_delete", args=[post.pk])).status_code, 404)
        self.assertEqual(Post.objects.count(), 1)

    def test_profile_and_search_pages_render(self):
        Post.objects.create(author=self.bob, content="findable text")
        self.assertEqual(self.client.get(reverse("profile", args=["bob"])).status_code, 200)
        self.assertContains(self.client.get(reverse("search") + "?q=findable"), "findable text")
        self.assertEqual(self.client.get(reverse("followers", args=["bob"])).status_code, 200)
