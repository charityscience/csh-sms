# csh-sms

#### Installation

Download [Postgressapp](https://postgresapp.com/) or otherwise download Postgres. You will need to put the app on your `PATH` to get access to the `psql` executible.

Within Postgres:

```
CREATE DATABASE cshsms;
CREATE ROLE cshsmsadmin;
ALTER ROLE cshsmsadmin WITH LOGIN;
ALTER ROLE cshsmsadmin CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE cshsms TO cshsmsadmin;
CREATE DATABASE test_cshsms;
ALTER DATABASE test_cshsms OWNER TO cshsmsadmin;
```

Then initialize Django:

```
pip install -r requirements.txt
python manage.py migrate
```


#### Run

Run Postgres then...

```
python manage.py runserver
```

To run tests...

```
python manage.py test
```
