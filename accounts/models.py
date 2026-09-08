"""User identity and authentication models, implementing Role-Based Access Control (RBAC)."""

from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager for the CustomUser model handling user creation logic."""

    def create_user(self, username, email, password=None, **extra_fields):
        """Create and save a standard user."""
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """Create a superuser with staff and superuser flags set to True."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Extends AbstractUser to include application-specific roles and subscriptions.
    Roles: Reader, Editor, Journalist, Publisher.
    """

    ROLE_CHOICES = (
        ("reader", "Reader"),
        ("editor", "Editor"),
        ("journalist", "Journalist"),
        ("publisher", "Publisher"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="reader")

    subscribed_publishers = models.ManyToManyField(
        "news.Publisher",
        related_name="subscribers",
        blank=True,
        help_text="Publishers this user is subscribed to",
    )
    subscribed_journalists = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="journalist_subscribers",
        blank=True,
        help_text="Journalists this user is subscribed to",
    )

    bio = models.TextField(blank=True, help_text="For journalists - short bio")
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        """Return username and the display name of the assigned role."""
        return f"{self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        """Overwrite save to synchronize the user's Django Group with their assigned role."""
        super().save(*args, **kwargs)

        if self.role:
            group_name = self.role.capitalize() + "s"
            group, _ = Group.objects.get_or_create(name=group_name)
            self.groups.add(group)

    @property
    def is_reader(self):
        """Check if the user is a reader."""
        return self.role == "reader"

    @property
    def is_editor(self):
        """Check if the user is an editor."""
        return self.role == "editor"

    @property
    def is_journalist(self):
        """Check if the user is a journalist."""
        return self.role == "journalist"

    @property
    def is_publisher(self):
        """Check if the user is a publisher."""
        return self.role == "publisher"
