#!/usr/bin/env python
import os
import sys

from fabric.context_managers import settings

from cshsms.settings import REMOTE
from fabfile import deploy, verify_server, read_server_log, fetch_server_log, kill_server

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cshsms.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise

    with settings(host_string=REMOTE['host'],
                  key_filename=REMOTE['keyfile'],
                  user=REMOTE['user']):
        if sys.argv[1] == "deploy":
            deploy()
        elif sys.argv[1] == "verify_server":
            verify_server()
        elif sys.argv[1] == "read_server_log":
            read_server_log()
        elif sys.argv[1] == "fetch_server_log":
            fetch_server_log()
        elif sys.argv[1] == "kill_server":
            kill_server()
        else:
            execute_from_command_line(sys.argv)
