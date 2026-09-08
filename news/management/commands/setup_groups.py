"""
Management command to set up groups and permissions.
Run with: python manage.py setup_groups
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = "Sets up groups and assigns permissions"

    def handle(self, *args, **options):
        # Reader group
        reader_group, _ = Group.objects.get_or_create(name="Readers")
        reader_permissions = [
            "view_article",
            "view_newsletter",
            "view_publisher",
        ]

        # Editor group
        editor_group, _ = Group.objects.get_or_create(name="Editors")
        editor_permissions = [
            "view_article",
            "add_article",
            "change_article",
            "delete_article",
            "view_newsletter",
            "add_newsletter",
            "change_newsletter",
            "delete_newsletter",
            "view_publisher",
            "add_publisher",
            "change_publisher",
            "can_approve_article",
            "can_publish_article",
        ]

        # Journalist group
        journalist_group, _ = Group.objects.get_or_create(name="Journalists")
        journalist_permissions = [
            "view_article",
            "add_article",
            "change_article",
            "delete_article",
            "view_newsletter",
            "add_newsletter",
            "change_newsletter",
            "delete_newsletter",
            "view_publisher",
        ]

        # Publisher group
        publisher_group, _ = Group.objects.get_or_create(name="Publishers")
        publisher_permissions = [
            "view_article",
            "view_publisher",
            "add_publisher",
            "change_publisher",
            "view_newsletter",
            "add_newsletter",
            "change_newsletter",
        ]

        # Assign permissions
        for group, perm_codenames in [
            (reader_group, reader_permissions),
            (editor_group, editor_permissions),
            (journalist_group, journalist_permissions),
            (publisher_group, publisher_permissions),
        ]:
            group.permissions.clear()
            for codename in perm_codenames:
                try:
                    perm = Permission.objects.get(codename=codename)
                    group.permissions.add(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Permission {codename} not found. Run migrations first."
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS("Successfully set up groups and permissions!")
        )
