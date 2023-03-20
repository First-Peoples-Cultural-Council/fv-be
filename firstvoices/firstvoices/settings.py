"""
Django settings for firstvoices project.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
from dotenv import load_dotenv

from . import database
from . import jwt

# .env file support
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-5^%n@uxu*tev&gyzsf-2_s8bdr#thg%qbtor3&k0zodl12j-1s'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.messages',
	'rest_framework',
	'backend'
]

MIDDLEWARE = [
	'django.contrib.sessions.middleware.SessionMiddleware', # ugh. sessions. required by admin.
	'django.middleware.security.SecurityMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'firstvoices.urls'

REST_FRAMEWORK = {
	# 'DEFAULT_AUTHENTICATION_CLASSES': (
	# 	'api.keycloak_authentication.UserAuthentication',),
	'DEFAULT_PARSER_CLASSES': (
		'djangorestframework_camel_case.parser.CamelCaseJSONParser',
	),
	'DEFAULT_RENDERER_CLASSES': (
		'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
	),
	'DEFAULT_AUTHENTICATION_CLASSES': [],
	'DEFAULT_PERMISSION_CLASSES': (
		'rest_framework.permissions.IsAuthenticated',),
	'UNAUTHENTICATED_USER': None

}

TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"APP_DIRS": True,
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

WSGI_APPLICATION = 'firstvoices.wsgi.application'

CACHES = {
	'default': {
		'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
	},
	'auth': {
		'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
		'LOCATION': 'auth',
	},
}

DATABASES = {
	'default': database.config()
}

AUTH_USER_MODEL = 'backend.User'

JWT = jwt.config()

LANGUAGE_CODE = 'en-ca'

TIME_ZONE = 'America/Vancouver'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
