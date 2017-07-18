
# SECURITY WARNING: keep the secret key used in production secret!
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
