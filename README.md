# csh-sms <a href="https://travis-ci.org/charityscience/csh-sms/builds"><img src="https://img.shields.io/travis/charityscience/csh-sms.svg"></a> <a href="https://codecov.io/github/charityscience/csh-sms"><img src="https://img.shields.io/codecov/c/github/charityscience/csh-sms.svg"></a>


#### Local Installation

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


#### Running

Run Postgres then...

```
python manage.py runserver
```

To run local unit tests...

```
python manage.py test tests/
```

To run local functional / live / E2E tests...

```
python manage.py test live_tests/
```

Warning: These live tests can take 1.7hrs to complete! Set `export CSHSMS_ENV=dev` to see test logging output during the test run.



#### Remote Installation

To set up the remote server from scratch:

1.) Create a box on AWS
2.) Update the `REMOTE` variable in `cshsms/settings_secret.py`
3.) Verify you can connect to the box with `python manage.py ssh_server` (then disconnect)
4.) Provision the box with `python manage.py remote_install`
5.) Deploy the code to the remote box with `python manage.py deploy`
6.) Verify the integrity of the server with `python manage.py verify_server`
7a.) Further verify with `python manage.py remote_live_tests` (warning: takes >1.5hrs).


#### Deployment and Remote Management


To deploy the existing server, run:

```
python manage.py deploy
```

(To set up a new remote server, configure the server on AWS, edit the `REMOTE` file in `cshsms/settings.py`, and then run `fab install`. Don't do this unless you know what you are doing.)

To verify the remote server is running correctly, run:

```
python manage.py verify_server
```

To run remote unit tests, run:

```
python manage.py remote_unit_tests
```

To run remote live tests (warning: takes >1.5hrs), run:

```
python manage.py remote_live_tests
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
