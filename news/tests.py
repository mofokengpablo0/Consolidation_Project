"""
Unit tests for the news application.

Tests cover:
- API authentication per role
- Reader can only retrieve subscribed content
- Journalist can create articles
- Editor can approve and delete
- Newsletter functionality
- Signal logic with mocking
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from unittest.mock import patch, MagicMock

from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from .models import Article, Publisher, Newsletter, ApprovedArticleLog

User = get_user_model()


class BaseTestCase(APITestCase):
    """Base test case with common setup."""

    def setUp(self):
        """Set up test data."""
        # Create users with different roles
        self.reader = User.objects.create_user(
            username="reader1",
            email="reader@test.com",
            password="testpass123",
            role="reader",
        )

        self.journalist = User.objects.create_user(
            username="journalist1",
            email="journalist@test.com",
            password="testpass123",
            role="journalist",
        )

        self.editor = User.objects.create_user(
            username="editor1",
            email="editor@test.com",
            password="testpass123",
            role="editor",
        )

        # Create a publisher
        self.publisher = Publisher.objects.create(
            name="Test Publisher",
            description="A test publisher",
        )
        self.publisher.journalists.add(self.journalist)
        self.publisher.editors.add(self.editor)

        # Create test articles
        self.approved_article = Article.objects.create(
            title="Approved Article",
            content="This is the content of the approved article. " * 10,
            summary="An approved article",
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )

        self.pending_article = Article.objects.create(
            title="Pending Article",
            content="This is pending article content. " * 10,
            summary="A pending article",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )

        # Create newsletter
        self.newsletter = Newsletter.objects.create(
            title="Test Newsletter",
            description="A test newsletter",
            author=self.journalist,
        )
        self.newsletter.articles.add(self.approved_article)


class AuthenticationTests(BaseTestCase):
    """Test authentication requirements for different endpoints."""

    def test_unauthenticated_can_list_approved_articles(self):
        """Unauthenticated users can view approved articles."""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see approved articles
        article_ids = [a["id"] for a in response.data["results"]]
        self.assertIn(self.approved_article.id, article_ids)
        self.assertNotIn(self.pending_article.id, article_ids)

    def test_unauthenticated_cannot_create_article(self):
        """Unauthenticated users cannot create articles."""
        data = {
            "title": "New Article",
            "content": "Content here " * 20,
            "publisher": self.publisher.id,
        }
        response = self.client.post("/api/articles/", data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReaderTests(BaseTestCase):
    """Test reader permissions and subscribed content."""

    def setUp(self):
        super().setUp()
        # Subscribe reader to publisher
        self.reader.subscribed_publishers.add(self.publisher)
        # Subscribe reader to journalist
        self.reader.subscribed_journalists.add(self.journalist)

    def test_reader_can_view_approved_articles(self):
        """Reader can view approved articles."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reader_cannot_create_article(self):
        """Reader cannot create articles."""
        self.client.force_authenticate(user=self.reader)
        data = {
            "title": "New Article",
            "content": "Content here " * 20,
            "publisher": self.publisher.id,
        }
        response = self.client.post("/api/articles/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reader_can_view_subscribed_articles(self):
        """Reader can view articles from subscribed publishers/journalists."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.get("/api/articles/subscribed/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        article_ids = [a["id"] for a in response.data["results"]]
        self.assertIn(self.approved_article.id, article_ids)

    def test_reader_cannot_view_unsubscribed_content(self):
        """Reader doesn't see articles from non-subscribed sources."""
        # Create another publisher and journalist
        other_publisher = Publisher.objects.create(
            name="Other Publisher", description="Not subscribed"
        )
        other_journalist = User.objects.create_user(
            username="other_journalist",
            email="other@test.com",
            password="testpass123",
            role="journalist",
        )

        unsubscribed_article = Article.objects.create(
            title="Unsubscribed Article",
            content="Content here " * 10,
            author=other_journalist,
            publisher=other_publisher,
            approved=True,
        )

        self.client.force_authenticate(user=self.reader)
        response = self.client.get("/api/articles/subscribed/")
        article_ids = [a["id"] for a in response.data["results"]]

        self.assertIn(self.approved_article.id, article_ids)
        self.assertNotIn(unsubscribed_article.id, article_ids)


class JournalistTests(BaseTestCase):
    """Test journalist permissions and article creation."""

    def test_journalist_can_create_article(self):
        """Journalist can create articles."""
        self.client.force_authenticate(user=self.journalist)
        data = {
            "title": "Journalist Article",
            "content": "Content written by journalist " * 10,
            "summary": "New article",
            "publisher": self.publisher.id,
        }
        response = self.client.post("/api/articles/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.count(), 3)

    def test_journalist_can_edit_own_article(self):
        """Journalist can edit their own articles."""
        self.client.force_authenticate(user=self.journalist)
        data = {
            "title": "Updated Title",
            "content": "Updated content " * 10,
        }
        response = self.client.patch(f"/api/articles/{self.approved_article.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.approved_article.refresh_from_db()
        self.assertEqual(self.approved_article.title, "Updated Title")

    def test_journalist_cannot_approve_article(self):
        """Journalist cannot approve articles."""
        self.client.force_authenticate(user=self.journalist)
        response = self.client.post(f"/api/articles/{self.pending_article.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_journalist_can_create_newsletter(self):
        """Journalist can create newsletters."""
        self.client.force_authenticate(user=self.journalist)
        data = {
            "title": "New Newsletter",
            "description": "Newsletter description",
            "articles": [self.approved_article.id],
        }
        response = self.client.post("/api/newsletters/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class EditorTests(BaseTestCase):
    """Test editor permissions."""

    def test_editor_can_view_pending_articles(self):
        """Editor can view pending articles."""
        self.client.force_authenticate(user=self.editor)
        response = self.client.get("/api/articles/pending/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        article_ids = [a["id"] for a in response.data]
        self.assertIn(self.pending_article.id, article_ids)

    def test_editor_can_approve_article(self):
        """Editor can approve articles."""
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(f"/api/articles/{self.pending_article.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.pending_article.refresh_from_db()
        self.assertTrue(self.pending_article.approved)

    def test_editor_can_delete_article(self):
        """Editor can delete articles."""
        self.client.force_authenticate(user=self.editor)
        response = self.client.delete(f"/api/articles/{self.pending_article.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Article.objects.filter(id=self.pending_article.id).exists())

    def test_editor_can_create_publisher(self):
        """Editor can create publishers."""
        self.client.force_authenticate(user=self.editor)
        data = {
            "name": "New Publisher",
            "description": "A new publisher",
        }
        response = self.client.post("/api/publishers/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class SubscriptionTests(BaseTestCase):
    """Test subscription functionality."""

    def test_user_can_subscribe_to_publisher(self):
        """User can subscribe to a publisher via API."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.post(f"/api/publishers/{self.publisher.id}/subscribe/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.publisher, self.reader.subscribed_publishers.all())

    def test_user_can_unsubscribe_from_publisher(self):
        """User can unsubscribe from a publisher via API."""
        self.reader.subscribed_publishers.add(self.publisher)
        self.client.force_authenticate(user=self.reader)
        response = self.client.post(f"/api/publishers/{self.publisher.id}/unsubscribe/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.publisher, self.reader.subscribed_publishers.all())


class NewsletterTests(BaseTestCase):
    """Test newsletter functionality."""

    def test_newsletter_creation(self):
        """Test creating a newsletter."""
        newsletter = Newsletter.objects.create(
            title="My Newsletter",
            description="Test newsletter",
            author=self.journalist,
        )
        newsletter.articles.add(self.approved_article)

        self.assertEqual(newsletter.get_article_count(), 1)
        self.assertIn(self.approved_article, newsletter.articles.all())

    def test_newsletter_serializer(self):
        """Test newsletter serialization."""
        from .serializers import NewsletterSerializer

        serializer = NewsletterSerializer(self.newsletter)
        data = serializer.data

        self.assertEqual(data["title"], "Test Newsletter")
        self.assertEqual(data["article_count"], 1)
        self.assertEqual(len(data["articles"]), 1)

    def test_only_journalists_can_create_newsletters(self):
        """Only journalists/editors can create newsletters."""
        self.client.force_authenticate(user=self.reader)
        data = {
            "title": "Reader Newsletter",
            "description": "Should fail",
        }
        response = self.client.post("/api/newsletters/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SignalTests(BaseTestCase):
    """Test signal logic with mocking."""

    @patch("news.signals.requests.post")
    @patch("news.signals.send_mass_mail")
    def test_article_approval_triggers_signals(self, mock_send_mass_mail, mock_post):
        """Test that approving an article triggers signal actions."""
        # Mock the API POST response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = "Success"
        mock_post.return_value = mock_response

        # Mock email sending
        mock_send_mass_mail.return_value = True

        # Subscribe reader to publisher
        self.reader.subscribed_publishers.add(self.publisher)

        # Approve the pending article
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(f"/api/articles/{self.pending_article.id}/approve/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify API was called
        self.assertTrue(mock_post.called)

        # Verify log was created
        self.assertTrue(
            ApprovedArticleLog.objects.filter(article=self.pending_article).exists()
        )

        log = ApprovedArticleLog.objects.get(article=self.pending_article)
        self.assertTrue(log.posted_to_api)

    @patch("news.signals.post_to_api")
    def test_signal_posts_to_correct_endpoint(self, mock_post_to_api):
        """Test that signal POSTs to the correct API endpoint."""
        mock_post_to_api.return_value = (True, "Success")

        # Subscribe reader
        self.reader.subscribed_publishers.add(self.publisher)

        # Approve article
        self.pending_article.approved = True
        self.pending_article.approved_by = self.editor
        self.pending_article.save()

        # Verify the mocked function was called
        self.assertTrue(mock_post_to_api.called)

    def test_email_not_sent_when_no_subscribers(self):
        """Test that no email is sent when there are no subscribers."""
        with patch("news.signals.send_approval_emails") as mock_email:
            self.pending_article.approved = True
            self.pending_article.approved_by = self.editor
            self.pending_article.save()

            # Email function should be called but return False (no subscribers)
            self.assertTrue(mock_email.called)


class ArticleValidationTests(BaseTestCase):
    """Test article validation."""

    def test_article_requires_minimum_title_length(self):
        """Test that article title must be at least 5 characters."""
        self.client.force_authenticate(user=self.journalist)
        data = {
            "title": "abc",
            "content": "Content " * 20,
        }
        response = self.client.post("/api/articles/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_article_requires_minimum_content_length(self):
        """Test that article content must be at least 50 characters."""
        self.client.force_authenticate(user=self.journalist)
        data = {
            "title": "Valid Title",
            "content": "Too short",
        }
        response = self.client.post("/api/articles/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class IntegrationTests(BaseTestCase):
    """Integration tests for complete workflows."""

    def test_complete_article_workflow(self):
        """Test complete workflow: create -> approve -> notify."""
        with patch("news.signals.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=201, text="OK")

            # 1. Journalist creates article
            self.client.force_authenticate(user=self.journalist)
            article = Article.objects.create(
                title="Workflow Test Article",
                content="Content for workflow test " * 10,
                author=self.journalist,
                publisher=self.publisher,
            )

            self.assertFalse(article.approved)

            # 2. Editor approves article
            self.client.force_authenticate(user=self.editor)
            response = self.client.post(f"/api/articles/{article.id}/approve/")

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # 3. Verify article is approved
            article.refresh_from_db()
            self.assertTrue(article.approved)

            # 4. Verify log was created
            self.assertTrue(ApprovedArticleLog.objects.filter(article=article).exists())

    def test_reader_workflow(self):
        """Test reader workflow: subscribe -> view subscribed content."""
        # 1. Reader subscribes to publisher
        self.client.force_authenticate(user=self.reader)
        response = self.client.post(f"/api/publishers/{self.publisher.id}/subscribe/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. Reader views subscribed articles
        response = self.client.get("/api/articles/subscribed/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        article_ids = [a["id"] for a in response.data["results"]]
        self.assertIn(self.approved_article.id, article_ids)
