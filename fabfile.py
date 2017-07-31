from __future__ import with_statement
from contextlib import contextmanager as _contextmanager

from fabric.api import env, sudo, run, prefix
from fabric.context_managers import cd
from fabric.operations import put
from fabric.colors import red, yellow

from cshsms.settings import DATABASES, REMOTE
USER = DATABASES['default']['USER']
DBNAME = DATABASES['default']['NAME']
PASSWORD =  DATABASES['default']['PASSWORD']

env.user = REMOTE['user']
env.key_filename = REMOTE['keyfile']
env.hosts = [REMOTE['host']]

@_contextmanager
def virtualenv():
    with cd("csh-sms"):
        with prefix("source /home/ubuntu/.virtualenvs/csh/bin/activate"):
            yield

def install():
    sudo("apt-get update")
    sudo("apt-get -y upgrade")
    sudo("apt-get -y install python-pip python-dev")
    sudo("apt-get -y install build-essential")
    sudo("apt-get -y install postgresql")
    sudo("psql -c 'CREATE DATABASE {};'".format(DBNAME), user="postgres")
    sudo("psql -c 'CREATE ROLE {};'".format(USER), user="postgres")
    sudo("psql -c 'ALTER ROLE {} WITH LOGIN;'".format(USER), user="postgres")
    sudo("psql -c \"ALTER USER {} WITH PASSWORD '{}'\"".format(USER, PASSWORD), user="postgres")
    sudo("psql -c 'ALTER ROLE {} WITH CREATEDB;'".format(USER), user="postgres")
    sudo("psql -c 'GRANT ALL PRIVILEGES ON DATABASE {} TO {};'".format(DBNAME, USER), user="postgres")
    run("git clone https://github.com/charityscience/csh-sms.git")
    run("pip install virtualenvwrapper")
    with prefix("export WORKON_HOME=$HOME/.virtualenvs"):
        with prefix("source /home/ubuntu/.local/bin/virtualenvwrapper.sh"):
            run("mkvirtualenv csh")
    with virtualenv():
        run("pip install -r requirements.txt")
        run("mkdir logs")
        run("touch logs/cshsms.log")
        put("cshsms/settings_secret.py", "/home/ubuntu/csh-sms/cshsms/settings_secret.py")
        

def deploy():
    with virtualenv():
        run("git reset HEAD --hard")
        run("git checkout master")
        run("git pull")
        run("pip install -r requirements.txt")
        run("python manage.py migrate")
        run("python manage.py test")
        run("python manage.py crontab add")


def verify_server():
    with virtualenv():
        print("Last deployment time was...")
        run("env TZ=':America/Los_Angeles' date -r cshsms/settings.py")
        print("Last log entry was...")
        run("env TZ=':America/Los_Angeles' date -r logs/cshsms.log")
        print("Last commit was...")
        run("git log -1 --format=%cd | cat")
        print("Checking crontab...")
        run("crontab -l")
        print("Verifying remote tests...")
        run("python manage.py test")

def read_server_log():
    with virtualenv():
        run("cat logs/cshsms.log")

def kill_server():
    with virtualenv():
        print(red("Shutting down the server..."))
        run("python manage.py crontab remove")
        print(red("Crontab now offline."))
        print(yellow("Note: The server is still running, but is idle and will no longer process texts or send reminders. Shut down the actual app via AWS to stop the server from running. The server can be re-enabled with `python manage.py deploy`."))
        print(yellow("Note: Future deploys will re-enable the server."))

