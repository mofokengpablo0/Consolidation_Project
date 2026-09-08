from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Article, Publisher, Newsletter, ApprovedArticleLog
from .serializers import (
    ArticleSerializer,
    ArticleListSerializer,
    PublisherSerializer,
    NewsletterSerializer,
    ApprovedArticleSerializer,
    UserSerializer,
)
from .permissions import (
    IsJournalist,
    IsEditor,
    IsPublisher,
    IsArticleAuthorOrEditor,
    CanApproveArticle,
    IsNewsletterAuthorOrEditor,
)

User = get_user_model()


# ============================================================
# AUTHENTICATION
# ============================================================


@api_view(["POST"])
@permission_classes([AllowAny])
def register_api(request):
    """Register a new user via API."""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Set password
        password = request.data.get("password")
        if password:
            user.set_password(password)
            user.save()

        # Generate token
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": serializer.data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# ARTICLE VIEWS
# ============================================================


class ArticleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Article.

    list: GET /api/articles/ - List approved articles (public)
    retrieve: GET /api/articles/{id}/ - Get specific article
    create: POST /api/articles/ - Create article (journalists only)
    update: PUT /api/articles/{id}/ - Update article (author/editor)
    delete: DELETE /api/articles/{id}/ - Delete article (author/editor)
    """

    queryset = Article.objects.all()
    permission_classes = [AllowAny]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action == "list":
            return ArticleListSerializer
        return ArticleSerializer

    def get_queryset(self):
        """Filter articles based on user role and action."""
        user = self.request.user

        if not user.is_authenticated:
            # Public users see only approved articles
            return Article.objects.filter(approved=True)

        if self.action == "list":
            if user.role == "editor":
                # Editors see all articles
                return Article.objects.all()
            elif user.role == "journalist":
                # Journalists see their own + approved articles
                return Article.objects.filter(
                    Q(author=user) | Q(approved=True)
                ).distinct()
            else:
                # Readers see only approved articles
                return Article.objects.filter(approved=True)

        return Article.objects.all()

    def get_permissions(self):
        if self.action == "create":
            return [IsJournalist()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsArticleAuthorOrEditor()]
        elif self.action == "approve":
            return [CanApproveArticle()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Set the author to the current user."""
        serializer.save(author=self.request.user)

    @action(detail=False, methods=["get"])
    def subscribed(self, request):
        """Get articles from publishers/journalists the user is subscribed to."""
        user = request.user

        # Get subscribed publishers
        subscribed_publishers = user.subscribed_publishers.all()

        # Get subscribed journalists
        subscribed_journalists = user.subscribed_journalists.all()

        # Get articles from these
        articles = (
            Article.objects.filter(approved=True)
            .filter(
                Q(publisher__in=subscribed_publishers)
                | Q(author__in=subscribed_journalists)
            )
            .distinct()
        )

        page = self.paginate_queryset(articles)
        if page is not None:
            serializer = ArticleListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def approve(self, request, id=None):
        """Approve an article (editors only)."""
        if request.user.role != "editor":
            return Response(
                {"error": "Only editors can approve articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        article = self.get_object()
        article.approved = True
        article.approved_by = request.user
        article.save()  # Triggers signal

        return Response(
            {
                "message": "Article approved successfully.",
                "article": ArticleSerializer(article).data,
            }
        )

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """Get pending (unapproved) articles (editors only)."""
        if request.user.role != "editor":
            return Response(
                {"error": "Only editors can view pending articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        pending_articles = Article.objects.filter(approved=False)
        serializer = ArticleListSerializer(pending_articles, many=True)
        return Response(serializer.data)


# ============================================================
# PUBLISHER VIEWS
# ============================================================


class PublisherViewSet(viewsets.ModelViewSet):
    """ViewSet for Publisher management."""

    queryset = Publisher.objects.filter(is_active=True)
    serializer_class = PublisherSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsEditor() | IsPublisher()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def subscribe(self, request, pk=None):
        """Subscribe current user to this publisher."""
        publisher = self.get_object()
        request.user.subscribed_publishers.add(publisher)
        return Response(
            {
                "message": f"Subscribed to {publisher.name}",
                "publisher": PublisherSerializer(publisher).data,
            }
        )

    @action(detail=True, methods=["post"])
    def unsubscribe(self, request, pk=None):
        """Unsubscribe current user from this publisher."""
        publisher = self.get_object()
        request.user.subscribed_publishers.remove(publisher)
        return Response({"message": f"Unsubscribed from {publisher.name}"})


# ============================================================
# NEWSLETTER VIEWS
# ============================================================


class NewsletterViewSet(viewsets.ModelViewSet):
    """ViewSet for Newsletter management."""

    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "create":
            return [IsJournalist()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsNewsletterAuthorOrEditor()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# ============================================================
# APPROVED ARTICLES LOG API ENDPOINT
# ============================================================


@api_view(["POST"])
@permission_classes([AllowAny])
def approved_articles_endpoint(request):
    """
    Internal API endpoint for receiving approved articles.
    This is the endpoint that signals POST to.
    """
    try:
        article_id = request.data.get("article_id")

        if not article_id:
            return Response(
                {"error": "article_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        article = Article.objects.get(id=article_id)

        # Log the approval
        log, created = ApprovedArticleLog.objects.get_or_create(article=article)

        # Update the log with API call info
        log.posted_to_api = True
        log.api_response = (
            f"Received at {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
        )
        log.save()

        return Response(
            {
                "message": "Article logged successfully",
                "article_id": article_id,
                "title": article.title,
                "received_at": log.created_at,
            },
            status=status.HTTP_201_CREATED,
        )

    except Article.DoesNotExist:
        return Response(
            {"error": "Article not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def approved_articles_list(request):
    """List all approved article logs."""
    logs = ApprovedArticleLog.objects.all().order_by("-created_at")
    serializer = ApprovedArticleSerializer(logs, many=True)
    return Response(serializer.data)


# ============================================================
# USER VIEWS
# ============================================================


class CurrentUserView(APIView):
    """Get current authenticated user info."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    """API root - shows available endpoints."""
    return Response(
        {
            "message": "Welcome to the News Application API",
            "version": "1.0",
            "endpoints": {
                "authentication": {
                    "register": "/api/register/",
                    "token": "/api/token/",
                    "token_refresh": "/api/token/refresh/",
                },
                "articles": {
                    "list": "/api/articles/",
                    "subscribed": "/api/articles/subscribed/",
                    "pending": "/api/articles/pending/",
                    "detail": "/api/articles/{id}/",
                    "approve": "/api/articles/{id}/approve/",
                },
                "publishers": {
                    "list": "/api/publishers/",
                    "subscribe": "/api/publishers/{id}/subscribe/",
                },
                "newsletters": "/api/newsletters/",
                "current_user": "/api/users/me/",
                "approved_log": {
                    "list": "/api/approved/",
                    "post": "/api/approved/",
                },
            },
        }
    )
