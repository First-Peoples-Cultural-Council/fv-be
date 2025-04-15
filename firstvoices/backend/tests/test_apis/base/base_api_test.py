import json


class WriteApiTestMixin:
    """Common functions for Create and Update API tests"""

    content_type = "application/json"

    def get_invalid_data(self):
        """Returns an invalid data object suitable for failing create/update requests"""
        return {}

    def get_valid_data(self, site=None):
        """Returns a valid data object suitable for create/update requests"""
        raise NotImplementedError

    def get_valid_data_with_nulls(self, site=None):
        """Returns a valid data object with all optional fields omitted (including strings that can be blank),
        suitable for create/update requests"""
        raise NotImplementedError

    def get_valid_data_with_null_optional_charfields(self, site=None):
        """Returns a valid data object that includes all optional charfields set to None"""
        raise NotImplementedError

    def add_expected_defaults(self, data):
        """Returns a data object with default values filled in for all non-required fields"""
        raise NotImplementedError

    def format_upload_data(self, data):
        """Subclasses can override this to support something other than json"""
        return json.dumps(data)
