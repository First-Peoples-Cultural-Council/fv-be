from django.contrib.auth import get_user_model
from rest_framework import serializers

REQUIRED_HEADERS = ["title", "type"]


def check_required_headers(input_headers):
    # check for the required headers

    input_headers = [h.strip().lower() for h in input_headers]
    if set(REQUIRED_HEADERS) - set(input_headers):
        raise serializers.ValidationError(
            detail={
                "data": [
                    "CSV file does not have the all the required headers. Required headers are ['title', 'type']"
                ]
            }
        )
    return True


def validate_username(username):
    user_model = get_user_model()
    username_field = user_model.USERNAME_FIELD
    user = user_model.objects.filter(**{username_field: username})
    if len(user) == 0:
        raise serializers.ValidationError(
            detail={"run_as_user": [f"Invalid {username_field}."]}
        )
    else:
        return user[0]
