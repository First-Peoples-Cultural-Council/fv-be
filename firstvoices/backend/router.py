from rest_framework.routers import DefaultRouter


class CustomRouter(DefaultRouter):
    """
    Similar to DefaultRouter, but supports URLs with or without trailing slashes.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trailing_slash = (
            "/?"  # trailing slashes are optional; urls are not modified
        )
