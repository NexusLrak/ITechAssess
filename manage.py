#!/usr/bin/env python3
import os
import sys
import django
from django.core.management import execute_from_command_line, call_command
from django.conf import settings


def main():
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nutrition_tracker.settings')

    django.setup()
    print(settings.DATABASES["default"]["NAME"])

    if os.environ.get("RUN_MAIN") != "true":
        call_command("migrate", interactive=False, verbosity=2)

    # execute_from_command_line(sys.argv)
    execute_from_command_line(["manage.py", "runserver", "8000"])



if __name__ == '__main__':
    main()
