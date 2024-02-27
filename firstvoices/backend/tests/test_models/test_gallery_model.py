import pytest
from django.db.utils import IntegrityError

from backend.models.constants import Visibility
from backend.tests import factories


class TestGalleryModel:
    @pytest.mark.django_db
    def test_galleries_can_use_same_image_as_cover(self):
        """Galleries can use the same image as their cover image"""
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        image = factories.ImageFactory.create(site=site)

        gallery = factories.GalleryFactory.create(site=site, cover_image=image)
        assert gallery.cover_image == image

        gallery2 = factories.GalleryFactory.create(site=site, cover_image=image)
        assert gallery2.cover_image == image


class TestGalleryImageModel:
    @pytest.mark.django_db
    def test_gallery_item_same_image(self):
        """Gallery item can't be created with an image already in the gallery"""
        gallery_item = factories.GalleryItemFactory.create()
        with pytest.raises(IntegrityError):
            factories.GalleryItemFactory.create(
                image=gallery_item.image, gallery=gallery_item.gallery
            )

    @pytest.mark.django_db
    def test_gallery_item_same_order(self):
        """Gallery item can't be created with the same order as another in the same gallery"""
        gallery_item = factories.GalleryItemFactory.create()
        with pytest.raises(IntegrityError):
            factories.GalleryItemFactory.create(
                gallery=gallery_item.gallery, ordering=gallery_item.ordering
            )
