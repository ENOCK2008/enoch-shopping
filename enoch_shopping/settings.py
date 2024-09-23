from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')  # Ensure this is kept secret in production
DEBUG = False  # Set to False in production
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '0.0.0.0',
    '[::1]', 
    'enoch-shopping-4.onrender.com'  # Replace with your actual Render domain
]

# Login and redirect URLs
LOGIN_REDIRECT_URL = 'shop:home'
LOGOUT_REDIRECT_URL = 'shop:home'
LOGIN_URL = '/shop/login/'  # Ensure this matches your login path

# Installed apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop',  # Your custom app
    'rest_framework',  # Django REST Framework
    'channels',  # Django Channels for WebSocket handling
    'django_otp',  # Django OTP for two-factor authentication
    'django_otp.plugins.otp_totp',  # Time-based One-Time Passwords (TOTP)
    'two_factor',  # Two-factor authentication
    'django_extensions',  # Extensions for Django
]

# Middleware settings
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL configuration
ROOT_URLCONF = 'enoch_shopping.urls'

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'shop/templates', BASE_DIR / 'two_factor/templates/auth_two_factor'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI and ASGI applications
WSGI_APPLICATION = 'enoch_shopping.wsgi.application'
ASGI_APPLICATION = 'enoch_shopping.asgi.application'  # ASGI for handling WebSocket connections

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Localization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
    # Add other languages here
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # Make sure this path exists

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Directory where static files will be collected
STATICFILES_DIRS = [
    BASE_DIR / 'enoch_shopping/static',  # Adjust this path if your static files are located elsewhere
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Application settings
APPEND_SLASH = True  # Ensures URLs are correctly routed with a trailing slash

# Stripe configuration (if you're using Stripe for payments)
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'your_stripe_secret_key')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', 'your_stripe_publishable_key')

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Use console backend for development
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.your-email-provider.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'your-email@example.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'your-email-password')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Mobile money configuration
MOBILE_MONEY_CONFIG = {
    'API_BASE_URL': os.getenv('MOBILE_MONEY_API_BASE_URL', 'https://api.example.com/'),
    'MPESA_API_KEY': os.getenv('MPESA_API_KEY', 'your_mpesa_api_key'),
    'MTN_API_KEY': os.getenv('MTN_API_KEY', 'your_mtn_api_key'),
    'AIRTEL_API_KEY': os.getenv('AIRTEL_API_KEY', 'your_airtel_api_key'),
}

# Django Channels settings
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],  # Ensure Redis is running here
        },
    },
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'chat_consumer.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'DEBUG',
    },
}

# Ensure the log directory exists
log_file_path = BASE_DIR / 'chat_consumer.log'
if not log_file_path.parent.exists():
    os.makedirs(log_file_path.parent)

# Secure settings for local development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Allows framing from the same origin only

# PayPal configuration
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')

# Use the PORT environment variable for deployment
PORT = os.environ.get('PORT', '8000')
