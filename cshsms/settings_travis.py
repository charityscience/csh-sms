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

TEXTLOCAL_API = os.getenv("TEXTLOCAL_API")
TEXTLOCAL_PRIMARY_ID = os.getenv("TEXTLOCAL_PRIMARY_ID")
TEXTLOCAL_PHONENUMBER = os.getenv("TEXTLOCAL_PHONENUMBER")
HSPSMS_API = os.getenv("HSPSMS_API")
HSPSMS_USERNAME = os.getenv("HSPSMS_USERNAME")
HSPSMS_SENDERNAME = os.getenv("HSPSMS_SENDERNAME")