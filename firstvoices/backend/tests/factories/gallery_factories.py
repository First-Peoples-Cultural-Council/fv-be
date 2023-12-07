import factory
from factory.django import DjangoModelFactory

from backend.models import Gallery, GalleryItem
from backend.tests.factories import ImageFactory, SiteFactory, UserFactory


class GalleryFactory(DjangoModelFactory):
    class Meta:
        model = Gallery

    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Gallery title %03d" % n)
    title_translation = factory.Sequence(lambda n: "Gallery title translation %03d" % n)
    cover_image = factory.SubFactory(ImageFactory)


class GalleryItemFactory(DjangoModelFactory):
    class Meta:
        model = GalleryItem

    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    gallery = factory.SubFactory(GalleryFactory)
    image = factory.SubFactory(ImageFactory)
    order = factory.Sequence(int)
