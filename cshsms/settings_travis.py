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

os.getenv("TEXTLOCAL_API")
os.getenv("TEXTLOCAL_PRIMARY_ID")