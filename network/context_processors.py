from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()


def suggestions(request):
    """People the signed-in user doesn't follow yet (shown in the right-hand column)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    people = (
        User.objects.exclude(pk=user.pk)
        .exclude(follower_links__follower=user)
        .select_related("profile")
        .annotate(n_followers=Count("follower_links"))
        .order_by("-n_followers", "-date_joined")[:5]
    )
    return {"suggested_people": people}
