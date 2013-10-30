"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()
user = lambda u: User.objects.get_by_natural_key(u)
permission = lambda id: Permission.objects.get(id=id)

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
