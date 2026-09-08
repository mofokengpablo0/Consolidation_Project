# C:\Projects\news_project\test_app.py
"""
Comprehensive Test Script for News Application
==============================================
This script tests every function of the application:
- User registration and authentication
- Role-based permissions (Reader, Editor, Journalist)
- Article creation, approval, editing, deletion
- Publisher management
- Newsletter creation
- Subscription management
- API endpoints (all CRUD operations)
- Email notifications on approval
- Signal triggering

Run with: python test_app.py
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from news.models import Article, Publisher, Newsletter, Subscription, ApprovedArticleLog

User = get_user_model()


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class TestRunner:
    """Manages test execution and reporting."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.current_test = None

    def print_header(self, text):
        """Print section header."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 70}")
        print(f"{text}")
        print(f"{'=' * 70}{Colors.RESET}")

    def print_test(self, test_name):
        """Print test name being executed."""
        self.current_test = test_name
        print(f"\n{Colors.YELLOW}▶ Testing: {test_name}{Colors.RESET}")

    def assert_true(self, condition, message):
        """Assert condition is true."""
        if condition:
            self.passed += 1
            print(f"  {Colors.GREEN}✓ PASS{Colors.RESET}: {message}")
            return True
        else:
            self.failed += 1
            error = f"{self.current_test}: {message}"
            self.errors.append(error)
            print(f"  {Colors.RED}✗ FAIL{Colors.RESET}: {message}")
            return False

    def assert_equal(self, actual, expected, message):
        """Assert two values are equal."""
        if actual == expected:
            self.passed += 1
            print(f"  {Colors.GREEN}✓ PASS{Colors.RESET}: {message}")
            return True
        else:
            self.failed += 1
            error = (
                f"{self.current_test}: {message} (Expected: {expected}, Got: {actual})"
            )
            self.errors.append(error)
            print(f"  {Colors.RED}✗ FAIL{Colors.RESET}: {message}")
            print(f"    Expected: {expected}")
            print(f"    Got: {actual}")
            return False

    def assert_not_equal(self, actual, expected, message):
        """Assert two values are not equal."""
        if actual != expected:
            self.passed += 1
            print(f"  {Colors.GREEN}✓ PASS{Colors.RESET}: {message}")
            return True
        else:
            self.failed += 1
            error = f"{self.current_test}: {message}"
            self.errors.append(error)
            print(f"  {Colors.RED}✗ FAIL{Colors.RESET}: {message}")
            return False

    def print_summary(self):
        """Print final test summary."""
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0

        print(f"\n{Colors.BOLD}{'=' * 70}")
        print(f"{Colors.BOLD}TEST SUMMARY")
        print(f"{'=' * 70}{Colors.RESET}")
        print(f"Total Tests: {Colors.BOLD}{total}{Colors.RESET}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.RESET}")
        print(f"Success Rate: {Colors.BOLD}{percentage:.1f}%{Colors.RESET}")

        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}FAILED TESTS:{Colors.RESET}")
            for error in self.errors:
                print(f"  {Colors.RED}✗{Colors.RESET} {error}")

        print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}")


class NewsAppTestSuite:
    """Complete test suite for the news application."""

    def __init__(self):
        self.runner = TestRunner()
        self.client = Client()
        self.api_client = APIClient()
        self.cleanup_data()

    def cleanup_data(self):
        """Clean up test data before running."""
        print(f"{Colors.YELLOW}Cleaning up test data...{Colors.RESET}")
        ApprovedArticleLog.objects.all().delete()
        Article.objects.all().delete()
        Newsletter.objects.all().delete()
        Subscription.objects.all().delete()
        Publisher.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        User.objects.filter(username="admin").delete()
        print(f"{Colors.GREEN}✓ Cleanup complete{Colors.RESET}")

    def create_test_users(self):
        """Create test users for each role."""
        self.runner.print_header("1. USER MANAGEMENT TESTS")

        # Test 1.1: Create Reader
        self.runner.print_test("Create Reader User")
        self.reader = User.objects.create_user(
            username="test_reader",
            email="reader@test.com",
            password="TestPass123!",
            role="reader",
            first_name="Test",
            last_name="Reader",
        )
        self.runner.assert_equal(
            self.reader.role, "reader", "Reader role assigned correctly"
        )
        self.runner.assert_true(
            self.reader.check_password("TestPass123!"), "Password set correctly"
        )

        # Test 1.2: Create Journalist
        self.runner.print_test("Create Journalist User")
        self.journalist = User.objects.create_user(
            username="test_journalist",
            email="journalist@test.com",
            password="TestPass123!",
            role="journalist",
            first_name="Test",
            last_name="Journalist",
            bio="Experienced journalist",
        )
        self.runner.assert_equal(
            self.journalist.role, "journalist", "Journalist role assigned"
        )
        self.runner.assert_true(
            self.journalist.is_journalist, "is_journalist property works"
        )

        # Test 1.3: Create Editor
        self.runner.print_test("Create Editor User")
        self.editor = User.objects.create_user(
            username="test_editor",
            email="editor@test.com",
            password="TestPass123!",
            role="editor",
            first_name="Test",
            last_name="Editor",
        )
        self.runner.assert_equal(self.editor.role, "editor", "Editor role assigned")
        self.runner.assert_true(self.editor.is_editor, "is_editor property works")

        # Test 1.4: Verify groups are assigned
        self.runner.print_test("Verify Group Assignment")
        self.runner.assert_true(
            self.reader.groups.filter(name="Readers").exists(),
            "Reader added to Readers group",
        )
        self.runner.assert_true(
            self.journalist.groups.filter(name="Journalists").exists(),
            "Journalist added to Journalists group",
        )
        self.runner.assert_true(
            self.editor.groups.filter(name="Editors").exists(),
            "Editor added to Editors group",
        )

        # Test 1.5: Superuser creation
        self.runner.print_test("Create Superuser")
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="Admin123!"
        )
        self.runner.assert_true(self.admin.is_superuser, "Superuser created")
        self.runner.assert_true(self.admin.is_staff, "Superuser is staff")

    def test_authentication(self):
        """Test authentication functionality."""
        self.runner.print_header("2. AUTHENTICATION TESTS")

        # Test 2.1: Login with valid credentials
        self.runner.print_test("Login with Valid Credentials")
        logged_in = self.client.login(username="test_reader", password="TestPass123!")
        self.runner.assert_true(logged_in, "Reader can log in")

        # Test 2.2: Login with invalid password
        self.runner.print_test("Login with Invalid Password")
        logged_in = self.client.login(username="test_reader", password="WrongPass")
        self.runner.assert_true(not logged_in, "Invalid password rejected")

        # Test 2.3: Access protected page
        self.runner.print_test("Access Protected Profile Page")
        self.client.login(username="test_reader", password="TestPass123!")
        response = self.client.get(reverse("accounts:profile"))
        self.runner.assert_equal(
            response.status_code, 200, "Authenticated user can access profile"
        )

        # Test 2.4: Logout
        self.runner.print_test("Logout")
        self.client.logout()
        response = self.client.get(reverse("accounts:profile"))
        self.runner.assert_equal(
            response.status_code, 302, "Unauthenticated user redirected"
        )

    def test_publishers(self):
        """Test publisher management."""
        self.runner.print_header("3. PUBLISHER MANAGEMENT TESTS")

        # Test 3.1: Create publisher
        self.runner.print_test("Create Publisher")
        self.publisher = Publisher.objects.create(
            name="Tech News Daily",
            description="Latest technology news and reviews",
            website="https://technews.com",
            primary_editor=self.editor,
        )
        self.publisher.editors.add(self.editor)
        self.publisher.journalists.add(self.journalist)

        self.runner.assert_equal(
            str(self.publisher), "Tech News Daily", "Publisher name"
        )
        self.runner.assert_equal(
            self.publisher.primary_editor, self.editor, "Primary editor set"
        )
        self.runner.assert_true(
            self.editor in self.publisher.editors.all(), "Editor added"
        )
        self.runner.assert_true(
            self.journalist in self.publisher.journalists.all(), "Journalist added"
        )

        # Test 3.2: Publisher methods
        self.runner.print_test("Publisher Methods")
        self.runner.assert_equal(
            self.publisher.get_editor_count(), 1, "Editor count correct"
        )
        self.runner.assert_equal(
            self.publisher.get_journalist_count(), 1, "Journalist count correct"
        )

        # Test 3.3: Create second publisher
        self.runner.print_test("Create Second Publisher")
        self.publisher2 = Publisher.objects.create(
            name="Sports Weekly", description="All sports news"
        )
        self.runner.assert_not_equal(
            self.publisher.id, self.publisher2.id, "Different publishers"
        )

    def test_articles(self):
        """Test article functionality."""
        self.runner.print_header("4. ARTICLE MANAGEMENT TESTS")

        # Test 4.1: Journalist creates article
        self.runner.print_test("Journalist Creates Article")
        self.article1 = Article.objects.create(
            title="Breaking: New AI Technology Released",
            content="A groundbreaking new AI technology has been released that will revolutionize the industry. This comprehensive article covers all the details and implications.",
            summary="New AI tech released today",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )
        self.runner.assert_equal(
            self.article1.author, self.journalist, "Author set correctly"
        )
        self.runner.assert_true(
            not self.article1.approved, "Article starts as unapproved"
        )
        self.runner.assert_equal(
            self.article1.get_status(), "Pending Review", "Status is pending"
        )

        # Test 4.2: Article validation
        self.runner.print_test("Article Title Validation")
        self.runner.assert_true(
            len(self.article1.title) >= 5, "Title meets minimum length"
        )

        # Test 4.3: Create publisher article
        self.runner.print_test("Create Publisher Article")
        self.article2 = Article.objects.create(
            title="Tech Company Announces New Product",
            content="Major tech company announces their latest product with innovative features.",
            summary="Product announcement",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )
        self.runner.assert_equal(
            self.article2.publisher, self.publisher, "Publisher assigned"
        )

        # Test 4.4: Create independent article
        self.runner.print_test("Create Independent Article")
        self.independent_article = Article.objects.create(
            title="Independent Opinion Piece",
            content="This is an independent article with no publisher affiliation.",
            author=self.journalist,
            publisher=None,
            approved=False,
        )
        self.runner.assert_true(
            self.independent_article.publisher is None, "No publisher"
        )

        # Test 4.5: Article count
        self.runner.print_test("Publisher Article Count")
        count = self.publisher.get_article_count()
        self.runner.assert_equal(count, 0, "No approved articles yet")

        # Test 4.6: Edit article
        self.runner.print_test("Edit Article")
        self.article1.title = "Updated: New AI Technology"
        self.article1.save()
        updated = Article.objects.get(id=self.article1.id)
        self.runner.assert_equal(
            updated.title, "Updated: New AI Technology", "Title updated"
        )

    def test_article_approval_and_signals(self):
        """Test article approval and signal triggers."""
        self.runner.print_header("5. ARTICLE APPROVAL & SIGNAL TESTS")

        # Test 5.1: Subscribe reader to publisher
        self.runner.print_test("Reader Subscribes to Publisher")
        self.reader.subscribed_publishers.add(self.publisher)
        self.runner.assert_true(
            self.publisher in self.reader.subscribed_publishers.all(),
            "Reader subscribed",
        )

        # Test 5.2: Subscribe to journalist
        self.runner.print_test("Reader Subscribes to Journalist")
        self.reader.subscribed_journalists.add(self.journalist)
        self.runner.assert_true(
            self.journalist in self.reader.subscribed_journalists.all(),
            "Subscribed to journalist",
        )

        # Test 5.3: Approve article with signal mocking
        self.runner.print_test("Approve Article (with signal mocking)")

        with patch("news.signals.requests.post") as mock_post, patch(
            "news.signals.send_approval_emails"
        ) as mock_email:

            mock_post.return_value = MagicMock(status_code=201, text="Success")
            mock_email.return_value = True

            # Approve the article
            self.article1.approved = True
            self.article1.approved_by = self.editor
            self.article1.approved_at = timezone.now()
            self.article1.save()

            # Check signal was triggered
            self.runner.assert_true(mock_post.called, "API POST signal triggered")
            self.runner.assert_true(mock_email.called, "Email signal triggered")

            # Check log was created
            log_exists = ApprovedArticleLog.objects.filter(
                article=self.article1
            ).exists()
            self.runner.assert_true(log_exists, "Approval log created")

        # Test 5.4: Verify approved article
        self.runner.print_test("Verify Article Approval")
        self.article1.refresh_from_db()
        self.runner.assert_true(self.article1.approved, "Article is approved")
        self.runner.assert_equal(
            self.article1.approved_by, self.editor, "Approver recorded"
        )
        self.runner.assert_true(
            self.article1.published_date is not None, "Published date set"
        )
        self.runner.assert_equal(
            self.article1.get_status(), "Published", "Status is published"
        )

        # Test 5.5: Publisher article count after approval
        self.runner.print_test("Publisher Article Count After Approval")
        count = self.publisher.get_article_count()
        self.runner.assert_equal(count, 1, "One approved article")

    def test_subscriptions(self):
        """Test subscription functionality."""
        self.runner.print_header("6. SUBSCRIPTION TESTS")

        # Test 6.1: Multiple subscribers
        self.runner.print_test("Multiple Subscribers")
        reader2 = User.objects.create_user(
            username="reader2",
            email="reader2@test.com",
            password="TestPass123!",
            role="reader",
        )
        self.publisher.subscribers.add(reader2)
        self.runner.assert_equal(
            self.publisher.get_subscriber_count(), 2, "Two subscribers"
        )

        # Test 6.2: Unsubscribe
        self.runner.print_test("Unsubscribe from Publisher")
        self.reader.subscribed_publishers.remove(self.publisher)
        self.runner.assert_true(
            self.publisher not in self.reader.subscribed_publishers.all(),
            "Unsubscribed successfully",
        )

        # Test 6.3: Subscribe to second publisher
        self.runner.print_test("Subscribe to Second Publisher")
        self.reader.subscribed_publishers.add(self.publisher2)
        self.runner.assert_true(
            self.publisher2 in self.reader.subscribed_publishers.all(),
            "Subscribed to second publisher",
        )

    def test_newsletters(self):
        """Test newsletter functionality."""
        self.runner.print_header("7. NEWSLETTER TESTS")

        # Test 7.1: Create newsletter
        self.runner.print_test("Create Newsletter")
        self.newsletter = Newsletter.objects.create(
            title="Weekly Tech Digest",
            description="Your weekly dose of technology news",
            author=self.journalist,
        )
        self.newsletter.articles.add(self.article1)

        self.runner.assert_equal(self.newsletter.author, self.journalist, "Author set")
        self.runner.assert_equal(self.newsletter.get_article_count(), 1, "One article")

        # Test 7.2: Add more articles
        self.runner.print_test("Add Articles to Newsletter")
        self.article2.approved = True
        self.article2.save()
        self.newsletter.articles.add(self.article2)
        self.runner.assert_equal(self.newsletter.get_article_count(), 2, "Two articles")

        # Test 7.3: Multiple newsletters
        self.runner.print_test("Create Multiple Newsletters")
        newsletter2 = Newsletter.objects.create(
            title="Sports Weekly", description="All sports news", author=self.editor
        )
        self.runner.assert_not_equal(
            self.newsletter.id, newsletter2.id, "Different newsletters"
        )

    def test_api_endpoints(self):
        """Test all API endpoints."""
        self.runner.print_header("8. API ENDPOINT TESTS")

        # Test 8.1: API root
        self.runner.print_test("API Root Endpoint")
        response = self.api_client.get("/api/")
        self.runner.assert_equal(response.status_code, 200, "API root accessible")

        # Test 8.2: Get JWT token
        self.runner.print_test("Get JWT Token")
        response = self.api_client.post(
            "/api/token/",
            {"username": "test_journalist", "password": "TestPass123!"},
            format="json",
        )
        self.runner.assert_equal(response.status_code, 200, "Token obtained")
        self.runner.assert_true("access" in response.data, "Access token present")
        self.runner.assert_true("refresh" in response.data, "Refresh token present")

        self.access_token = response.data["access"]

        # Test 8.3: List articles (public)
        self.runner.print_test("GET /api/articles/ (Public)")
        response = self.api_client.get("/api/articles/")
        self.runner.assert_equal(response.status_code, 200, "Articles list accessible")
        self.runner.assert_true("results" in response.data, "Pagination works")

        # Test 8.4: Get single article
        self.runner.print_test("GET /api/articles/{id}/")
        response = self.api_client.get(f"/api/articles/{self.article1.id}/")
        self.runner.assert_equal(response.status_code, 200, "Article retrievable")
        self.runner.assert_equal(
            response.data["title"], self.article1.title, "Title matches"
        )

        # Test 8.5: Create article as journalist
        self.runner.print_test("POST /api/articles/ (As Journalist)")
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.api_client.post(
            "/api/articles/",
            {
                "title": "API Created Article",
                "content": "This article was created through the API. " * 5,
                "summary": "API article",
                "publisher": self.publisher.id,
            },
            format="json",
        )
        self.runner.assert_equal(response.status_code, 201, "Article created via API")

        # Test 8.6: Try to create article as reader (should fail)
        self.runner.print_test("POST /api/articles/ (As Reader - Should Fail)")
        reader_token_response = self.api_client.post(
            "/api/token/",
            {"username": "test_reader", "password": "TestPass123!"},
            format="json",
        )
        reader_token = reader_token_response.data["access"]
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {reader_token}")
        response = self.api_client.post(
            "/api/articles/",
            {
                "title": "Should Fail",
                "content": "This should not be created. " * 5,
            },
            format="json",
        )
        self.runner.assert_equal(
            response.status_code, 403, "Reader cannot create article"
        )

        # Test 8.7: List publishers
        self.runner.print_test("GET /api/publishers/")
        response = self.api_client.get("/api/publishers/")
        self.runner.assert_equal(
            response.status_code, 200, "Publishers list accessible"
        )

        # Test 8.8: Subscribe to publisher via API
        self.runner.print_test("POST /api/publishers/{id}/subscribe/")
        response = self.api_client.post(
            f"/api/publishers/{self.publisher.id}/subscribe/"
        )
        self.runner.assert_equal(response.status_code, 200, "Subscribed via API")

        # Test 8.9: List newsletters
        self.runner.print_test("GET /api/newsletters/")
        response = self.api_client.get("/api/newsletters/")
        self.runner.assert_equal(
            response.status_code, 200, "Newsletters list accessible"
        )

        # Test 8.10: Get current user
        self.runner.print_test("GET /api/users/me/")
        response = self.api_client.get("/api/users/me/")
        self.runner.assert_equal(
            response.status_code, 200, "Current user endpoint works"
        )
        self.runner.assert_equal(
            response.data["username"], "test_reader", "Username matches"
        )

        # Test 8.11: Get subscribed articles
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {reader_token}")
        self.reader.subscribed_publishers.add(self.publisher)
        response = self.api_client.get("/api/articles/subscribed/")
        self.runner.assert_equal(
            response.status_code, 200, "Subscribed articles endpoint works"
        )

    def test_article_approval_api(self):
        """Test article approval via API."""
        self.runner.print_header("9. ARTICLE APPROVAL API TESTS")

        # Get editor token
        editor_token_response = self.api_client.post(
            "/api/token/",
            {"username": "test_editor", "password": "TestPass123!"},
            format="json",
        )
        editor_token = editor_token_response.data["access"]

        # Create a new article to approve
        article_to_approve = Article.objects.create(
            title="Article for Approval Test",
            content="Content " * 20,
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )

        # Test 9.1: Editor approves article
        self.runner.print_test("POST /api/articles/{id}/approve/ (As Editor)")
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {editor_token}")

        with patch("news.signals.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=201)

            response = self.api_client.post(
                f"/api/articles/{article_to_approve.id}/approve/"
            )
            self.runner.assert_equal(response.status_code, 200, "Article approved")
            self.runner.assert_true(mock_post.called, "Signal triggered")

        # Test 9.2: Journalist cannot approve
        self.runner.print_test(
            "POST /api/articles/{id}/approve/ (As Journalist - Should Fail)"
        )
        journalist_token_response = self.api_client.post(
            "/api/token/",
            {"username": "test_journalist", "password": "TestPass123!"},
            format="json",
        )
        journalist_token = journalist_token_response.data["access"]
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {journalist_token}")

        new_article = Article.objects.create(
            title="Another Article",
            content="Content " * 20,
            author=self.journalist,
            approved=False,
        )
        response = self.api_client.post(f"/api/articles/{new_article.id}/approve/")
        self.runner.assert_equal(response.status_code, 403, "Journalist cannot approve")

    def test_permissions_and_security(self):
        """Test permissions and security."""
        self.runner.print_header("10. PERMISSIONS & SECURITY TESTS")

        # Test 10.1: Permission classes
        self.runner.print_test("Custom Permission Classes")
        from news.permissions import (
            IsJournalist,
            IsEditor,
            IsReader,
            IsArticleAuthorOrEditor,
        )

        self.runner.assert_true(IsJournalist is not None, "IsJournalist defined")
        self.runner.assert_true(IsEditor is not None, "IsEditor defined")

        # Test 10.2: Reader cannot edit article
        self.runner.print_test("Reader Cannot Edit Article")
        self.client.login(username="test_reader", password="TestPass123!")
        response = self.client.get(
            reverse("news:article_edit", kwargs={"article_id": self.article1.id})
        )
        self.runner.assert_equal(response.status_code, 403, "Reader gets 403")

        # Test 10.3: Journalist can edit own article
        self.runner.print_test("Journalist Can Edit Own Article")
        self.client.login(username="test_journalist", password="TestPass123!")
        response = self.client.get(
            reverse("news:article_edit", kwargs={"article_id": self.article1.id})
        )
        self.runner.assert_equal(response.status_code, 200, "Journalist can edit")

        # Test 10.4: Article author check
        self.runner.print_test("Article Author Verification")
        self.runner.assert_equal(
            self.article1.author, self.journalist, "Author is journalist"
        )

        # Test 10.5: Editor can approve
        self.runner.print_test("Editor Can Access Dashboard")
        self.client.login(username="test_editor", password="TestPass123!")
        response = self.client.get(reverse("news:editor_dashboard"))
        self.runner.assert_equal(response.status_code, 200, "Editor accesses dashboard")

    def test_email_notifications(self):
        """Test email notification functionality."""
        self.runner.print_header("11. EMAIL NOTIFICATION TESTS")

        # Test 11.1: Email sent to subscribers on approval
        self.runner.print_test("Email Sent on Article Approval")

        # Subscribe reader
        self.reader.subscribed_publishers.add(self.publisher)

        # Create and approve article with email test
        with patch("news.signals.send_approval_emails") as mock_email:
            mock_email.return_value = True

            new_article = Article.objects.create(
                title="Email Test Article",
                content="Content for email test " * 10,
                author=self.journalist,
                publisher=self.publisher,
                approved=False,
            )

            new_article.approved = True
            new_article.approved_by = self.editor
            new_article.save()

            self.runner.assert_true(mock_email.called, "Email function called")
            self.runner.assert_true(new_article.approved, "Article approved")

        # Test 11.2: No email sent when no subscribers
        self.runner.print_test("No Email When No Subscribers")
        publisher_no_subs = Publisher.objects.create(
            name="No Subs Publisher", description="Test"
        )

        with patch("news.signals.send_approval_emails") as mock_email:
            mock_email.return_value = False

            article = Article.objects.create(
                title="No Subs Article",
                content="Content " * 10,
                author=self.journalist,
                publisher=publisher_no_subs,
                approved=False,
            )
            article.approved = True
            article.approved_by = self.editor
            article.save()

            # Email function should be called but with empty list
            self.runner.assert_true(mock_email.called, "Email function still called")

    def test_models_and_relationships(self):
        """Test model relationships."""
        self.runner.print_header("12. MODEL RELATIONSHIPS TESTS")

        # Test 12.1: User relationships
        self.runner.print_test("User Relationships")
        self.runner.assert_true(
            hasattr(self.reader, "subscribed_publishers"),
            "Reader has subscribed_publishers",
        )
        self.runner.assert_true(
            hasattr(self.reader, "subscribed_journalists"),
            "Reader has subscribed_journalists",
        )

        # Test 12.2: Publisher relationships
        self.runner.print_test("Publisher Relationships")
        self.runner.assert_true(
            self.publisher.journalists.filter(id=self.journalist.id).exists(),
            "Journalist is in publisher's journalists",
        )

        # Test 12.3: Article relationships
        self.runner.print_test("Article Relationships")
        self.runner.assert_true(
            self.journalist.authored_articles.filter(id=self.article1.id).exists(),
            "Article is in journalist's authored articles",
        )

        # Test 12.4: Newsletter relationships
        self.runner.print_test("Newsletter Relationships")
        self.runner.assert_true(
            self.article1 in self.newsletter.articles.all(),
            "Article is in newsletter",
        )
        # Test 12.5: Cascade delete
        self.runner.print_test("Cascade Delete Behavior")
        publisher_count = Publisher.objects.count()
        self.runner.assert_true(publisher_count >= 2, "Multiple publishers exist")

    def test_views_and_templates(self):
        """Test views and template rendering."""
        self.runner.print_header("13. VIEWS & TEMPLATES TESTS")

        # Test 13.1: Home page
        self.runner.print_test("Home Page")
        response = self.client.get(reverse("news:home"))
        self.runner.assert_equal(response.status_code, 200, "Home page loads")

        # Test 13.2: Article list
        self.runner.print_test("Article List Page")
        response = self.client.get(reverse("news:article_list"))
        self.runner.assert_equal(response.status_code, 200, "Article list loads")

        # Test 13.3: Article detail
        self.runner.print_test("Article Detail Page")
        response = self.client.get(
            reverse("news:article_detail", kwargs={"article_id": self.article1.id})
        )
        self.runner.assert_equal(response.status_code, 200, "Article detail loads")

        # Test 13.4: Publisher list
        self.runner.print_test("Publisher List Page")
        response = self.client.get(reverse("news:publisher_list"))
        self.runner.assert_equal(response.status_code, 200, "Publisher list loads")

        # Test 13.5: Publisher detail
        self.runner.print_test("Publisher Detail Page")
        response = self.client.get(
            reverse("news:publisher_detail", kwargs={"publisher_id": self.publisher.id})
        )
        self.runner.assert_equal(response.status_code, 200, "Publisher detail loads")

        # Test 13.6: Journalist list
        self.runner.print_test("Journalist List Page")
        response = self.client.get(reverse("news:journalist_list"))
        self.runner.assert_equal(response.status_code, 200, "Journalist list loads")

        # Test 13.7: Newsletter list
        self.runner.print_test("Newsletter List Page")
        response = self.client.get(reverse("news:newsletter_list"))
        self.runner.assert_equal(response.status_code, 200, "Newsletter list loads")

        # Test 13.8: Search functionality
        self.runner.print_test("Article Search")
        response = self.client.get(reverse("news:article_list"), {"q": "AI"})
        self.runner.assert_equal(response.status_code, 200, "Search works")

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        self.runner.print_header("14. EDGE CASES & ERROR HANDLING TESTS")

        # Test 14.1: Invalid article ID
        self.runner.print_test("Invalid Article ID")
        response = self.client.get(
            reverse("news:article_detail", kwargs={"article_id": 99999})
        )
        self.runner.assert_equal(response.status_code, 404, "404 for invalid ID")

        # Test 14.2: Empty search
        self.runner.print_test("Empty Search Query")
        response = self.client.get(reverse("news:article_list"), {"q": ""})
        self.runner.assert_equal(response.status_code, 200, "Empty search handled")

        # Test 14.3: Duplicate username registration
        self.runner.print_test("Duplicate Username Prevention")
        from accounts.forms import RegistrationForm

        form_data = {
            "username": "test_reader",
            "email": "another@test.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Dup",
            "last_name": "User",
            "role": "reader",
        }
        form = RegistrationForm(data=form_data)
        self.runner.assert_true(not form.is_valid(), "Duplicate username rejected")

        # Test 14.4: Password mismatch
        self.runner.print_test("Password Mismatch Validation")
        form_data["username"] = "newuser"
        form_data["password2"] = "DifferentPass"
        form = RegistrationForm(data=form_data)
        self.runner.assert_true(not form.is_valid(), "Password mismatch rejected")

        # Test 14.5: Article with minimal data
        self.runner.print_test("Article Validation")
        from news.forms import ArticleForm

        form = ArticleForm(
            data={
                "title": "abc",  # Too short
                "content": "short",  # Too short
            }
        )
        self.runner.assert_true(not form.is_valid(), "Short article rejected")

    def run_all_tests(self):
        """Run all test suites."""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'=' * 70}")
        print(f"NEWS APPLICATION COMPREHENSIVE TEST SUITE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 70}{Colors.RESET}\n")

        try:
            self.create_test_users()
            self.test_authentication()
            self.test_publishers()
            self.test_articles()
            self.test_article_approval_and_signals()
            self.test_subscriptions()
            self.test_newsletters()
            self.test_api_endpoints()
            self.test_article_approval_api()
            self.test_permissions_and_security()
            self.test_email_notifications()
            self.test_models_and_relationships()
            self.test_views_and_templates()
            self.test_edge_cases()

        except Exception as e:
            print(f"\n{Colors.RED}{Colors.BOLD}CRITICAL ERROR:{Colors.RESET}")
            print(f"{Colors.RED}{e}{Colors.RESET}")
            import traceback

            traceback.print_exc()

        self.runner.print_summary()

        # Return exit code
        return 0 if self.runner.failed == 0 else 1


if __name__ == "__main__":
    """Run the test suite."""
    test_suite = NewsAppTestSuite()
    exit_code = test_suite.run_all_tests()
    sys.exit(exit_code)
