import re

from django.core.exceptions import ValidationError

# A list of strings that are not allowed in SitePage slugs
RESERVED_SITE_PAGE_SLUG_LIST = [
    "apps",
    "categories",
    "dictionary",
    "games",
    "keyboards",
    "kids",
    "phrases",
    "songs",
    "stories",
    "words",
]


def reserved_site_page_slug_validator(slug):
    """
    This validator ensures that a SitePage slug does not contain any of the reserved strings.
    """
    for reserved_item in RESERVED_SITE_PAGE_SLUG_LIST:
        if bool(re.search(reserved_item, slug)):
            raise ValidationError(
                f"{slug} is a reserved slug or contains a reserved string."
            )


def validate_no_duplicate_urls(urls):
    """
    This validator ensures that a list of urls does not contain any duplicates.
    """
    if len(urls) != len(set(urls)):
        raise ValidationError("Duplicate urls found in list.")
