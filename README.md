# csh-sms <a href="https://travis-ci.org/charityscience/csh-sms/builds"><img src="https://img.shields.io/travis/charityscience/csh-sms.svg"></a> <a href="https://codecov.io/github/charityscience/csh-sms"><img src="https://img.shields.io/codecov/c/github/charityscience/csh-sms.svg"></a>

#### Installation

1.) Acquire a copy of `settings_secret.py` and put it in `cshsms/settings_secret.py`

2.) Download [Postgressapp](https://postgresapp.com/) or otherwise download Postgres. You will need to put the app on your `PATH` to get access to the `psql` executible.

3.) Within Postgres:

```
CREATE DATABASE cshsms;
CREATE ROLE cshsmsadmin;
ALTER ROLE cshsmsadmin WITH LOGIN;
ALTER ROLE cshsmsadmin CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE cshsms TO cshsmsadmin;
CREATE DATABASE test_cshsms;
ALTER DATABASE test_cshsms OWNER TO cshsmsadmin;
```

4.) Initialize Django:

```
pip install -r requirements.txt
mkdir logs
touch logs/cshsms.log
python manage.py migrate
```

5.) Install the relevant cronjobs (you probably only want to do this if you are prod):

```
python manage.py crontab add
```

Logs can be checked at `logs/cshsms.log`.


#### Run

Run Postgres then...

```
python manage.py runserver
```

To run tests...

```
python manage.py test
```


#### Deployment


To deploy the existing server, run:

```
python manage.py deploy
```

(To set up a new remote server, configure the server on AWS, edit the `REMOTE` file in `cshsms/settings.py`, and then run `fab install`. Don't do this unless you know what you are doing.)

To verify the remote server is running correctly, run:

```
python manage.py verify_server
```

To read the last twenty server logs:

```
python manage.py read_server_log
```

To download a copy of the server logs (downloaded to `logs/server_log.log`):

```
python manage.py fetch_server_log
```

To connect to the server directly:

```
python manage.py ssh_server
```

To stop the server from running:

```
python manage.py kill_server
```

This will idle processes and prevent anything from running (no texts will be processed and no reminders will be sent), but it will not shutdown the actual server. To do this, you must stop or terminate the box from within AWS.
