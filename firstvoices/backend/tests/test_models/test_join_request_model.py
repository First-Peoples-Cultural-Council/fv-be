import pytest
from django.db.utils import IntegrityError

from backend.tests.factories import JoinRequestFactory


class TestJoinRequestModel:
    @pytest.mark.django_db
    def test_join_request_same_user(self):
        """Join request can't be created with the same user and site as another"""
        join_request = JoinRequestFactory.create()
        with pytest.raises(IntegrityError):
            JoinRequestFactory.create(site=join_request.site, user=join_request.user)
