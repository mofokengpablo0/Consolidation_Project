"""
Signals for the news app.

When an article is approved:
1. Email subscribers of the journalist/publisher
2. POST to our own RESTful API endpoint (/api/approved/)
"""
"""Django signals for automating emails and API notifications upon article approval."""

import requests
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.core.mail import send_mass_mail, EmailMessage
from django.conf import settings
from .models import Article, ApprovedArticleLog

# Custom signal for article approval
article_approved = Signal()


@receiver(pre_save, sender=Article)
def track_approval_status(sender, instance, **kwargs):
    """Determine if an article's status is changing from unapproved to approved."""
    if instance.pk:
        try:
            old_instance = Article.objects.get(pk=instance.pk)
            if not old_instance.approved and instance.approved:
                instance._just_approved = True
                from django.utils import timezone

                instance.approved_at = timezone.now()
        except Article.DoesNotExist:
            pass


@receiver(post_save, sender=Article)
def handle_article_approval(sender, instance, created, **kwargs):
    """Execute post-approval workflow: email subscribers, API POST, and logging."""
    if not getattr(instance, "_just_approved", False):
        return

    subscribers = get_article_subscribers(instance)

    # Send emails to subscribers
    email_sent = False
    try:
        email_sent_result = send_approval_emails(instance, subscribers)
        email_sent = bool(email_sent_result)
    except Exception as e:
        print(f"Error sending emails: {e}")

    # POST to our own API endpoint
    api_success = False
    api_response = ""
    try:
        api_success, api_response = post_to_api(instance)
    except Exception as e:
        api_response = str(e)

    # Log the activity
    ApprovedArticleLog.objects.update_or_create(
        article=instance,
        defaults={
            "posted_to_api": api_success,
            "api_response": api_response,
            "emailed_to_subscribers": email_sent,
            "subscribers_count": len(subscribers),
        },
    )

    # Trigger custom signal
    article_approved.send(sender=Article, article=instance, subscribers=subscribers)


def get_article_subscribers(article):
    """Collect all unique users subscribed to either the article's publisher or author."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    subscribers = set()

    if article.publisher:
        for user in article.publisher.subscribers.filter(is_active=True):
            subscribers.add(user)

    for user in article.author.journalist_subscribers.filter(is_active=True):
        subscribers.add(user)

    return list(subscribers)


def send_approval_emails(article, subscribers):
    """Send personalized HTML email notifications to a list of subscribers."""
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags

    if not subscribers:
        return False

    subject = f"New Article: {article.title}"
    from_email = settings.DEFAULT_FROM_EMAIL
    messages = []

    for subscriber in subscribers:
        if subscriber.email:
            html_content = render_to_string(
                "news/article_approved.html",
                {"article": article, "subscriber": subscriber},
            )
            text_content = strip_tags(html_content)

            email = EmailMessage(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[subscriber.email],
            )
            messages.append(email)

    if messages:
        connection = messages[0].get_connection()
        connection.open()
        connection.send_messages(messages)
        connection.close()
        return True

    return False


def post_to_api(article):
    """Simulate sharing an approved article by POSTing it to an internal API endpoint."""
    api_url = f"http://127.0.0.1:8000/api/approved/"
    payload = {
        "article_id": article.id,
        "title": article.title,
        "content": article.content,
        "summary": article.summary,
        "author": article.author.username,
        "publisher": article.publisher.name if article.publisher else None,
        "approved_at": article.approved_at.isoformat() if article.approved_at else None,
    }
    headers = {"Content-Type": "application/json", "User-Agent": "NewsApp-Internal/1.0"}

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        return (
            response.status_code == 201,
            f"Status: {response.status_code}, Response: {response.text[:200]}",
        )
    except requests.exceptions.RequestException as e:
        return (False, f"Request failed: {str(e)}")
