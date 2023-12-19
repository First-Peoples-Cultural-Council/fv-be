import factory
from factory.django import DjangoModelFactory

from backend.models import Gallery, GalleryItem
from backend.tests.factories import ImageFactory, SiteFactory, UserFactory


class GalleryFactory(DjangoModelFactory):
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Gallery title %03d" % n)
    cover_image = factory.SubFactory(ImageFactory)

    class Meta:
        model = Gallery


class GalleryItemFactory(DjangoModelFactory):
    image = factory.SubFactory(ImageFactory)
    order = factory.Sequence(int)

    class Meta:
        model = GalleryItem
