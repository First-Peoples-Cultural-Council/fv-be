import factory

from backend.models.organizations import Organization
from backend.tests.factories import BaseSiteContentFactory


class OrganizationFactory(BaseSiteContentFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: "Organization %03d" % n)
