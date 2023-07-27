import os

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from backend.models.app import AppMembership
from backend.models.constants import AppRole

# This script creates a super admin membership model and is called in the reset-local-database.sh script.

email = os.getenv("DJANGO_SUPERUSER_EMAIL")
user = get_user_model().objects.filter(email=email).first()

try:
    membership = AppMembership(user=user, role=AppRole.SUPERADMIN)
    membership.save()
except IntegrityError as e:
    if "unique constraint" in e.args[0]:  # Check if it is a unique constraint violation
        print(
            "Superuser membership already added with the given DJANGO_SUPERUSER_EMAIL."
        )
