import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nutrition_tracker.settings")
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

call_command("migrate", interactive=False)

User = get_user_model()

u, created = User.objects.get_or_create(username="admin")

u.set_password("admin123")
u.is_superuser = True
u.is_staff = True
u.save()

call_command("runserver", "8000")

