from __future__ import with_statement
from contextlib import contextmanager as _contextmanager

from fabric.api import env, sudo, run, local, prefix, hide, settings
from fabric.colors import green, yellow, red
from fabric.context_managers import cd
from fabric.operations import put, get

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
        run("python manage.py crontab remove")
        run("git reset HEAD --hard")
        run("git fetch")
        run("git checkout master")
        run("git pull")
        run("pip install -r requirements.txt")
        run("python manage.py migrate")
        run("python manage.py test tests/")
        run("python manage.py crontab add")


def ssh_server():
    local("ssh -i {pemfile} {user}@{server}".format(pemfile=env.key_filename,
                                                    user=env.user,
                                                    server=env.hosts[0]))


def verify_server():
    with virtualenv():
        with hide('output', 'running', 'warnings'), settings(warn_only=True):
            last_deploy_time = run("env TZ=':America/Los_Angeles' date -r cshsms/settings.py")
            print("Last deployment time was {}.".format(last_deploy_time))
            last_log_entry_time = run("env TZ=':America/Los_Angeles' date -r logs/cshsms.log")
            print("Last log entry was {}.".format(last_log_entry_time))
            last_commit_time = run("git log -1 --format=%cd | cat")
            print("Last commit was {}.".format(last_commit_time))
            crontab = run("crontab -l")
            if len(crontab) == 0:
                print(red("Crontab is offline!"))
            else:
                print(green("Crontab installed and running..."))
                print(crontab)
        print("Verifying remote unit tests...")
        run("python manage.py test tests/")


def run_remote_unit_tests():
    with virtualenv():
        print("Verifying remote unit tests...")
        run("python manage.py test tests/")


def run_remote_live_tests():
    with virtualenv():
        print("Verifying remote live tests...")
        run("env CSHSMS_ENV=dev python manage.py test live_tests/")


def read_server_log():
    with virtualenv():
        with hide('output', 'running', 'warnings'), settings(warn_only=True):
            logs = run("tail -n 20 logs/cshsms.log")
            print(logs)

def fetch_server_log():
    with virtualenv():
        with hide('output', 'running', 'warnings'), settings(warn_only=True):
            print("Downloading server logs...")
            get("logs/cshsms.log", "logs/server_log.log")
            print("...Downloaded to `logs/server_log.log`")


def kill_server():
    with virtualenv():
        with settings(warn_only=True):
            print(red("Shutting down the server..."))
            run("killall python")
            run("python manage.py crontab remove")
            print(red("Server now offline."))
            run("python manage.py crontab remove")
            print(red("Crontab now offline."))
            print(yellow("Note: The server is still running, but is idle and will no longer process texts or send reminders. Shut down the actual app via AWS to stop the server from running. The server can be re-enabled with `python manage.py deploy`."))
            print(yellow("Note: Future deploys will re-enable the server."))
