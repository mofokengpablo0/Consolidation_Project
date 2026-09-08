"""REST Framework serializers for converting News and User models to JSON."""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Article, Publisher, Newsletter, Subscription, ApprovedArticleLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serialize basic User profile information."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "bio"]
        read_only_fields = ["id"]


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize Publisher details along with editor/journalist counts."""

    editors = UserSerializer(many=True, read_only=True)
    journalists = UserSerializer(many=True, read_only=True)
    article_count = serializers.SerializerMethodField()
    subscriber_count = serializers.SerializerMethodField()

    class Meta:
        model = Publisher
        fields = [
            "id",
            "name",
            "description",
            "logo",
            "website",
            "editors",
            "journalists",
            "article_count",
            "subscriber_count",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_article_count(self, obj):
        """Retrieve approved article count for the publisher."""
        return obj.get_article_count()

    def get_subscriber_count(self, obj):
        """Retrieve total subscriber count for the publisher."""
        return obj.get_subscriber_count()


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize detailed Article information and handle content validation."""

    author = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    publisher_name = serializers.CharField(source="publisher.name", read_only=True)
    status = serializers.CharField(source="get_status", read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "summary",
            "author",
            "publisher",
            "publisher_name",
            "approved",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
            "published_date",
            "image",
            "status",
        ]
        read_only_fields = [
            "id",
            "author",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
            "published_date",
        ]

    def validate_title(self, value):
        """Ensure the article title is at least 5 characters long."""
        if len(value) < 5:
            raise serializers.ValidationError(
                "Title must be at least 5 characters long."
            )
        return value

    def validate_content(self, value):
        """Ensure the article content is at least 50 characters long."""
        if len(value) < 50:
            raise serializers.ValidationError(
                "Article content must be at least 50 characters long."
            )
        return value


class ArticleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Article lists to reduce payload size."""

    author_username = serializers.CharField(source="author.username", read_only=True)
    publisher_name = serializers.CharField(source="publisher.name", read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "summary",
            "author_username",
            "publisher_name",
            "approved",
            "created_at",
            "published_date",
        ]


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize Newsletter details and its associated articles."""

    author = UserSerializer(read_only=True)
    articles = ArticleListSerializer(many=True, read_only=True)
    article_count = serializers.SerializerMethodField()

    class Meta:
        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "author",
            "articles",
            "article_count",
            "created_at",
            "updated_at",
            "sent_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_article_count(self, obj):
        """Retrieve total count of articles in the newsletter."""
        return obj.get_article_count()


class ApprovedArticleSerializer(serializers.ModelSerializer):
    """Serialize logs for articles that have been approved and pushed to API."""

    class Meta:
        model = ApprovedArticleLog
        fields = [
            "article",
            "posted_to_api",
            "api_response",
            "emailed_to_subscribers",
            "subscribers_count",
            "created_at",
        ]
        read_only_fields = ["posted_to_api", "created_at"]
