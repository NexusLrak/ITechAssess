import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nutrition_tracker.settings")
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

call_command("migrate", interactive=False)

User = get_user_model()

u = User.objects.get(username="admin")
u.set_password("admin123")
u.save()

call_command("runserver", "8000")