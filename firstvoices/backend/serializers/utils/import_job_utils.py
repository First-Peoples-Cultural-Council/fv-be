from django.contrib.auth import get_user_model
from rest_framework import serializers

REQUIRED_HEADERS = ["title", "type"]
REQUIRED_UPDATE_HEADERS = ["id"]


def check_required_headers(input_headers, update_mode=False):
    # check for the required headers
    required_headers = REQUIRED_HEADERS
    if update_mode:
        required_headers = REQUIRED_UPDATE_HEADERS

    input_headers = [h.strip().lower() for h in input_headers]
    if set(required_headers) - set(input_headers):
        raise serializers.ValidationError(
            detail={
                "data": [
                    f"CSV file does not have the all the required headers. Required headers are {required_headers}"
                ]
            }
        )
    return True


def check_duplicate_headers(input_headers):
    # check for any duplicate headers

    input_headers = [h.strip().lower() for h in input_headers]

    unique_headers = []
    duplicate_headers = []

    for header in input_headers:
        if header not in unique_headers:
            unique_headers.append(header)
        elif header not in duplicate_headers:
            duplicate_headers.append(header)

    if len(duplicate_headers):
        duplicate_headers_str = ",".join(str(header) for header in duplicate_headers)
        raise serializers.ValidationError(
            detail={
                "data": [
                    f"CSV file contains duplicate headers: {duplicate_headers_str}."
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
