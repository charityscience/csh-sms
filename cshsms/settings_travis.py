import os

SECRET_KEY = 'LONGstringOFsecrets'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'travisdb',
        'USER': 'travis',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '',
    }
}

REMOTE = {'user': 'travis',
          'keyfile': '~/.ssh/travis.pem',
          'host': 'localhost'}

TEXTLOCAL_API = "travis"
TEXTLOCAL_PRIMARY_ID = "travis"
HSPSMS_API = "travis"
HSPSMS_USERNAME = "travis"
HSPSMS_SENDERNAME = "travis"
TEXTLOCAL_SENDERNAME = "travis"
TEXTLOCAL_PHONENUMBER = "1111111111"
