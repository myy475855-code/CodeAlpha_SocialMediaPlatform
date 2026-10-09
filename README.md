# CodeAlpha_SocialMediaPlatform

**Tidepool** — a mini social media app built with Django for CodeAlpha Full Stack Development Internship, **Task 2**.

## Task requirements → where they live

| Requirement | Implementation |
|---|---|
| User profiles | `Profile` model (bio, location, website, avatar), `/u/<username>/`, `/settings/profile/` |
| Posts & comments | `Post` (text + optional image) and `Comment` models, post detail page with comments |
| Like system | `Like` model, AJAX toggle on every post (works without JS too) |
| Follow system | `Follow` model, follow/unfollow, followers / following lists, "Following" feed |
| Auth | Django auth: sign up, log in, log out |
| Database | SQLite (users, profiles, posts, comments, likes, follows) |
| Frontend | HTML templates, CSS, vanilla JavaScript |

Extras: search for people/posts, pagination, who-to-follow suggestions, delete own posts/comments, image upload validation (5 MB), responsive layout, automated tests.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations network
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Open http://127.0.0.1:8000/ , sign up, then try:
1. Create two accounts (use a private window for the second).
2. Follow each other, post, like, and comment.
3. Edit your profile and upload an avatar.

Run the tests: `python manage.py test`

## Project layout

```
socialsite/        project settings and root URLs
network/           the app: models, views, forms, urls, admin, tests
templates/         base layout, feed, profile, post detail, auth pages
static/            css/style.css, js/app.js
media/             uploaded avatars and post images (created at runtime)
```

## Notes
- Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` and `DJANGO_ALLOWED_HOSTS` before deploying anywhere public. Uploaded media is only served by Django in debug mode.
- Fonts load from Google Fonts; the app falls back to system fonts offline.
