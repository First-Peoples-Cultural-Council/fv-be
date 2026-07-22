import factory

from backend.models.contact_info import ContactInfo, TeamMember
from backend.tests.factories import BaseSiteContentFactory, SiteFactory


class ContactInfoFactory(BaseSiteContentFactory):
    class Meta:
        model = ContactInfo

    site = factory.SubFactory(SiteFactory)
    organization_name = factory.Sequence(lambda n: "Organization %03d" % n)
    emails = factory.List([factory.Sequence(lambda n: f"email{n}@example.com")])


class TeamMemberFactory(BaseSiteContentFactory):
    class Meta:
        model = TeamMember

    name = factory.Sequence(lambda n: "Team Member %03d" % n)
    organization_info = factory.SubFactory(
        ContactInfoFactory, site=factory.SelfAttribute("..site")
    )
