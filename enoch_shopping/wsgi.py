"""
WSGI config for the Enoch Shopping project.

This module exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Set the default settings module for the 'environ' variable.
# Make sure to replace 'enoch_shopping.settings' with your actual settings module if needed.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enoch_shopping.settings')

# Get the WSGI application for the project.
application = get_wsgi_application()
