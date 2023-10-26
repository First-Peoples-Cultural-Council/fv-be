import factory
from factory.django import DjangoModelFactory

from backend.models import JoinRequest
from backend.models.join_request import JoinRequestReason
from backend.tests.factories import SiteFactory, UserFactory


class JoinRequestFactory(DjangoModelFactory):
    class Meta:
        model = JoinRequest

    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    user = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)


class JoinRequestReasonFactory(DjangoModelFactory):
    class Meta:
        model = JoinRequestReason
