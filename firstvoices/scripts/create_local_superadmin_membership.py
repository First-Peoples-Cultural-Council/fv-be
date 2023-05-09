import os

from backend.models import User
from backend.models.app import AppMembership
from backend.models.constants import AppRole

# This script creates a super admin membership model and is called in the reset-local-database.sh script.

id = os.getenv("DJANGO_SUPERUSER_EMAIL")
user = User.objects.filter(id=id).first()

membership = AppMembership(user=user, role=AppRole.SUPERADMIN)
membership.save()
