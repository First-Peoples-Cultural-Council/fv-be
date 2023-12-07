import pytest
from django.db.utils import IntegrityError

from backend.tests.factories import GalleryItemFactory


class TestGalleryImageModel:
    @pytest.mark.django_db
    def test_gallery_item_same_image(self):
        """Gallery item can't be created with an image already in the gallery"""
        gallery_item = GalleryItemFactory.create()
        with pytest.raises(IntegrityError):
            GalleryItemFactory.create(
                image=gallery_item.image, gallery=gallery_item.gallery
            )

    @pytest.mark.django_db
    def test_gallery_item_same_order(self):
        """Gallery item can't be created with the same order as another in the same gallery"""
        gallery_item = GalleryItemFactory.create()
        with pytest.raises(IntegrityError):
            GalleryItemFactory.create(
                gallery=gallery_item.gallery, order=gallery_item.order
            )
