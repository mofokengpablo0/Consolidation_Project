"""Custom REST Framework permission classes for role-based access control."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsJournalist(BasePermission):
    """Grant access only to users with the 'journalist' role."""

    def has_permission(self, request, view):
        """Check if authenticated user is a journalist."""
        if not request.user.is_authenticated:
            return False
        return request.user.role == "journalist"


class IsEditor(BasePermission):
    """Grant access only to users with the 'editor' role."""

    def has_permission(self, request, view):
        """Check if authenticated user is an editor."""
        if not request.user.is_authenticated:
            return False
        return request.user.role == "editor"


class IsReader(BasePermission):
    """Grant access only to users with the 'reader' role."""

    def has_permission(self, request, view):
        """Check if authenticated user is a reader."""
        if not request.user.is_authenticated:
            return False
        return request.user.role == "reader"


class IsPublisher(BasePermission):
    """Grant access only to users with the 'publisher' role."""

    def has_permission(self, request, view):
        """Check if authenticated user is a publisher."""
        if not request.user.is_authenticated:
            return False
        return request.user.role == "publisher"


class IsEditorOrReadOnly(BasePermission):
    """Allow read-only access for all; restrict write access to editors."""

    def has_permission(self, request, view):
        """Check if request is a safe method or user is an editor."""
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == "editor"


class IsArticleAuthorOrEditor(BasePermission):
    """Allow editing/deletion if the user is the article's author or an editor."""

    def has_object_permission(self, request, view, obj):
        """Check object-level permission based on authorship or editor role."""
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user or (
            request.user.is_authenticated and request.user.role == "editor"
        )


class CanApproveArticle(BasePermission):
    """Restrict article approval functionality to editors only."""

    def has_permission(self, request, view):
        """Check if authenticated user is an editor."""
        return request.user.is_authenticated and request.user.role == "editor"


class IsNewsletterAuthorOrEditor(BasePermission):
    """Allow editing of newsletters if the user is the author or an editor."""

    def has_object_permission(self, request, view, obj):
        """Check object-level permission for newsletters."""
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user or (
            request.user.is_authenticated and request.user.role == "editor"
        )
