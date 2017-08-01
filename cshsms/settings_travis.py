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
HSPSMS_API = os.getenv("HSPSMS_API")