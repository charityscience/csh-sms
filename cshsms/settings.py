"""
Django settings for cshsms project.

Generated by 'django-admin startproject' using Django 1.11.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import logging
import sys
import os


if not os.getenv('IS_TRAVIS', False):
    from cshsms.settings_secret import SECRET_KEY, DATABASES, REMOTE, TEXTLOCAL_PHONENUMBER
else:
    from cshsms.settings_travis import SECRET_KEY, DATABASES, REMOTE, TEXTLOCAL_PHONENUMBER

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/



# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [REMOTE['host']]


INSTALLED_APPS = [
    'management.apps.ManagementConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_crontab'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cshsms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'cshsms.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_URL = '/static/'

TEST_RUNNER = 'rainbowtests.test.runner.RainbowDiscoverRunner'


# Logging (log all errors to .log file and ERRORs to console as well)
logger = logging.getLogger()
logging_format = "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
logfile = os.path.join(BASE_DIR, 'logs', 'cshsms.log')
logging.basicConfig(filename=logfile, level=logging.INFO, format=logging_format)
logging_handler_out = logging.StreamHandler(sys.stdout)
logging_handler_out.setLevel(logging.ERROR)
logging_handler_out.setFormatter(logging.Formatter(logging_format))
logger.addHandler(logging_handler_out)
CRONJOBS = [
    ('*/10 * * * *', 'jobs.text_reminder_job.remind_all'),                   # Run every 10 min
    ('5 4 * * *', 'jobs.text_processor_job.check_and_process_registrations') # Run daily at 4:05am
]
