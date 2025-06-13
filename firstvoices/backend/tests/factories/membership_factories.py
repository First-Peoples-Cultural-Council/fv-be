import factory

from backend.models import Membership
from backend.tests.factories import UserFactory
from backend.tests.factories.base_factories import BaseSiteContentFactory


class MembershipFactory(BaseSiteContentFactory):
    class Meta:
        model = Membership

    user = factory.SubFactory(UserFactory)
