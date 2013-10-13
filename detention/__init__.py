from django import VERSION
from django.core.exceptions import ImproperlyConfigured
if VERSION[:2] < (1, 5):
    raise ImproperlyConfigured("Django 1.5 is required for detention application to work")