import factory
from factory.django import DjangoModelFactory

from backend.models import JoinRequest
from backend.models.join_request import JoinRequestReason
from backend.tests.factories import UserFactory
from backend.tests.factories.base_factories import SiteContentFactory


class JoinRequestFactory(SiteContentFactory):
    class Meta:
        model = JoinRequest

    user = factory.SubFactory(UserFactory)


class JoinRequestReasonFactory(DjangoModelFactory):
    join_request = factory.SubFactory(JoinRequestFactory)

    class Meta:
        model = JoinRequestReason
