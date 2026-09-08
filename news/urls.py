"""URL routing configuration for the News application."""

from django.urls import path
from . import views

app_name = "news"

urlpatterns = [
    # Articles
    path("", views.home, name="home"),
    path("articles/", views.article_list, name="article_list"),
    path("articles/create/", views.article_create, name="article_create"),
    path("articles/<int:article_id>/", views.article_detail, name="article_detail"),
    path("articles/<int:article_id>/edit/", views.article_edit, name="article_edit"),
    path(
        "articles/<int:article_id>/delete/", views.article_delete, name="article_delete"
    ),
    path(
        "articles/<int:article_id>/approve/",
        views.article_approve,
        name="article_approve",
    ),
    # Publishers
    path("publishers/", views.publisher_list, name="publisher_list"),
    path(
        "publishers/<int:publisher_id>/",
        views.publisher_detail,
        name="publisher_detail",
    ),
    path(
        "publishers/<int:publisher_id>/subscribe/",
        views.subscribe_publisher,
        name="subscribe_publisher",
    ),
    # Journalists
    path("journalists/", views.journalist_list, name="journalist_list"),
    path(
        "journalists/<int:journalist_id>/",
        views.journalist_detail,
        name="journalist_detail",
    ),
    path(
        "journalists/<int:journalist_id>/subscribe/",
        views.subscribe_journalist,
        name="subscribe_journalist",
    ),
    # Newsletters
    path("newsletters/", views.newsletter_list, name="newsletter_list"),
    path("newsletters/create/", views.newsletter_create, name="newsletter_create"),
    path(
        "newsletters/<int:newsletter_id>/",
        views.newsletter_detail,
        name="newsletter_detail",
    ),
    # Editor dashboard
    path("editor/dashboard/", views.editor_dashboard, name="editor_dashboard"),
]
