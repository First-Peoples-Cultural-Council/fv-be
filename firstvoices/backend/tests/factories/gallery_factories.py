import factory
from factory.django import DjangoModelFactory

from backend.models import Gallery, GalleryItem
from backend.tests.factories import ImageFactory
from backend.tests.factories.base_factories import BaseSiteContentFactory


class GalleryFactory(BaseSiteContentFactory):
    class Meta:
        model = Gallery

    title = factory.Sequence(lambda n: "Gallery title %03d" % n)
    cover_image = factory.SubFactory(ImageFactory)


class GalleryItemFactory(DjangoModelFactory):
    gallery = factory.SubFactory(GalleryFactory)
    image = factory.SubFactory(ImageFactory)
    ordering = factory.Sequence(int)

    class Meta:
        model = GalleryItem
