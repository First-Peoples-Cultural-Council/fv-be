from backend.models.media import Person
from backend.resources.base import SiteContentResource


class PersonResource(SiteContentResource):
    class Meta:
        model = Person
