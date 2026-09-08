from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """Manager for CustomUser model with email as the identifier."""

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        self._assign_role_group(user)

        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "editor")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)

    def _assign_role_group(self, user):
        """Add the user to the Django auth Group matching their role."""
        from django.contrib.auth.models import Group

        role = getattr(user, "role", None)
        if not role:
            return

        group_name = f"{role.capitalize()}s"  # reader -> Readers, editor -> Editors
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
