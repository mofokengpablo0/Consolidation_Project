"""Core models for the news application, including Articles, Publishers, and Newsletters."""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


class Publisher(models.Model):
    """Represents a news publication entity managing editors and journalists."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    logo = models.ImageField(upload_to="publisher_logos/", blank=True, null=True)
    website = models.URLField(blank=True)

    primary_editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_publishers",
        limit_choices_to={"role__in": ["editor"]},
        help_text="Primary editor responsible for this publisher",
    )

    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="editor_publishers",
        limit_choices_to={"role__in": ["editor"]},
        blank=True,
        help_text="Editors who can approve articles for this publisher",
    )
    journalists = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="journalist_publishers",
        limit_choices_to={"role__in": ["journalist"]},
        blank=True,
        help_text="Journalists who write for this publisher",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Publishers"

    def __str__(self):
        """Return the publisher's name."""
        return self.name

    def get_article_count(self):
        """Return count of approved articles belonging to this publisher."""
        return self.articles.filter(approved=True).count()

    def get_subscriber_count(self):
        """Return the total number of subscribers."""
        return self.subscribers.count()

    def get_editor_count(self):
        """Return the number of associated editors."""
        return self.editors.count()

    def get_journalist_count(self):
        """Return the number of associated journalists."""
        return self.journalists.count()


class Article(models.Model):
    """Represents a news piece authored by a journalist, optionally tied to a publisher."""

    title = models.CharField(max_length=300)
    content = models.TextField()
    summary = models.TextField(
        max_length=500, blank=True, help_text="Brief summary of the article"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_articles",
        limit_choices_to={"role__in": ["journalist"]},
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name="articles",
        null=True,
        blank=True,
        help_text="Leave blank for independent articles",
    )

    approved = models.BooleanField(
        default=False, help_text="Whether this article has been approved by an editor"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_articles",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(null=True, blank=True)

    image = models.ImageField(upload_to="article_images/", blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("can_approve_article", "Can approve articles"),
            ("can_publish_article", "Can publish articles"),
        ]

    def __str__(self):
        """Return the article title."""
        return self.title

    def clean(self):
        """Validate that only users with the journalist role can author articles."""
        if self.author_id and self.author.role != "journalist":
            raise ValidationError("Only journalists can author articles.")

    def save(self, *args, **kwargs):
        """Overwrite save to automatically set published_date upon approval."""
        if self.approved and not self.published_date:
            self.published_date = timezone.now()
        super().save(*args, **kwargs)

    def get_status(self):
        """Return a human-readable status based on approval state."""
        if self.approved:
            return "Published"
        return "Pending Review"


class Newsletter(models.Model):
    """Represents a curated collection of articles sent to users."""

    title = models.CharField(max_length=200)
    description = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_newsletters",
        limit_choices_to={"role__in": ["journalist", "editor"]},
    )
    articles = models.ManyToManyField(
        Article,
        related_name="newsletters",
        help_text="Articles included in this newsletter",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """Return the newsletter title."""
        return self.title

    def get_article_count(self):
        """Return the number of articles included in the newsletter."""
        return self.articles.count()


class Subscription(models.Model):
    """Records subscription events between users and publishers/journalists."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions"
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subscription_records",
    )
    journalist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="journalist_subscription_records",
    )
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ("user", "publisher"),
            ("user", "journalist"),
        ]

    def __str__(self):
        """Return a string representation of the subscription."""
        target = self.publisher or self.journalist
        return f"{self.user.username} -> {target}"


class ApprovedArticleLog(models.Model):
    """Logs the external API transmission and notification status of approved articles."""

    article = models.OneToOneField(
        Article, on_delete=models.CASCADE, related_name="api_log"
    )
    posted_to_api = models.BooleanField(default=False)
    api_response = models.TextField(blank=True)
    emailed_to_subscribers = models.BooleanField(default=False)
    subscribers_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string referencing the logged article."""
        return f"Log for: {self.article.title}"
