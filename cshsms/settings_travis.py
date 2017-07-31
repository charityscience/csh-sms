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

# TextLocal
TEXTLOCAL_API = 'secretKeyisStillSoosecret'
TEXTLOCAL_PRIMARY_ID = 'SoSecrety'