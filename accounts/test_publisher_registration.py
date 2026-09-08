from django.test import SimpleTestCase

from accounts.models import CustomUser


class PublisherRegistrationRoleTests(SimpleTestCase):
    def test_publisher_role_is_available_in_role_choices(self):
        role_codes = dict(CustomUser.ROLE_CHOICES)
        self.assertIn("publisher", role_codes)
        self.assertEqual(role_codes["publisher"], "Publisher")
