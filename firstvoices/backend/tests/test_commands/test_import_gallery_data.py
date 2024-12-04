import uuid
from unittest.mock import patch

import pytest
import tablib
from django.core.management import call_command

from backend.models import Gallery, GalleryItem
from backend.tests import factories


class TestImportGalleryData:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "id,created,created_by,last_modified,last_modified_by,title,"
            "description,state,site,related_audio,related_images,related_videos"
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    def test_import_gallery_data_invalid_filepath(self):
        with pytest.raises(ValueError) as e:
            call_command("import_gallery_data", filepath="invalid/filepath")
        assert "Filepath invalid/filepath does not exist." in str(e)

    def test_import_gallery_data_no_csv_files(self, tmp_path):
        temp_dir = tmp_path / "no_files"
        temp_dir.mkdir(parents=True)
        with pytest.raises(ValueError) as e:
            call_command("import_gallery_data", filepath=temp_dir)
        assert "No CSV files found in the specified directory." in str(e)

    @pytest.mark.django_db
    def test_import_gallery_data(self, tmp_path, caplog):
        site = factories.SiteFactory.create()
        image1 = factories.ImageFactory.create(site=site)
        image2 = factories.ImageFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,testuser@test.com,2023-02-02 21:21:39.864,testuser@test.com,"
            f'Test Gallery 1,Description 1,Published,{site.id},,"{image1.id},{image2.id}",'
        ]
        table = self.build_table(data)
        filepath = tmp_path / "gallery.csv"
        with open(filepath, "w") as file:
            file.write(table.export("csv"))
        call_command("import_gallery_data", filepath=tmp_path)

        assert Gallery.objects.filter(site=site).count() == 1
        gallery = Gallery.objects.first()
        assert gallery.title == "Test Gallery 1"
        assert gallery.introduction == "Description 1"
        assert GalleryItem.objects.filter(gallery=gallery).count() == 2

        assert "Found 1 gallery CSV files to process." in caplog.text
        assert f"Processing file: {filepath}" in caplog.text
        assert "Gallery import completed." in caplog.text
        assert "File gallery.csv imported successfully." in caplog.text

    @pytest.mark.django_db
    def test_import_gallery_data_with_missing_image(self, tmp_path, caplog):
        site = factories.SiteFactory.create()
        non_existent_image_id = uuid.uuid4()
        valid_image = factories.ImageFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,testuser@test.com,2023-02-02 21:21:39.864,testuser@test.com,"
            f'Test Gallery 1,Description 1,Published,{site.id},,"{non_existent_image_id},{valid_image.id}",'
        ]
        table = self.build_table(data)
        filepath = tmp_path / "gallery.csv"
        with open(filepath, "w") as file:
            file.write(table.export("csv"))
        call_command("import_gallery_data", filepath=tmp_path)

        assert Gallery.objects.filter(site=site).count() == 1
        gallery = Gallery.objects.first()
        assert gallery.title == "Test Gallery 1"
        assert gallery.introduction == "Description 1"
        assert GalleryItem.objects.filter(gallery=gallery).count() == 1

        assert (
            f"Image with id {non_existent_image_id} not found. Skipping GalleryItem creation."
            in caplog.text
        )

    @pytest.mark.django_db
    def test_import_gallery_data_import_errors(self, tmp_path, caplog):
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,testuser@test.com,2023-02-02 21:21:39.864,testuser@test.com,"
            f"Test Gallery 1,Description 1,Published,{uuid.uuid4()},,,"
        ]
        table = self.build_table(data)
        filepath = tmp_path / "gallery.csv"
        with open(filepath, "w") as file:
            file.write(table.export("csv"))
        call_command("import_gallery_data", filepath=tmp_path)

        assert Gallery.objects.all().count() == 0
        assert GalleryItem.objects.count() == 0

        assert "Errors encountered while importing gallery.csv:" in caplog.text
        assert (
            "Row 1: <Error: DoesNotExist('Site matching query does not exist.')"
            in caplog.text
        )
        assert "Gallery import completed." in caplog.text

    @pytest.mark.django_db
    def test_import_gallery_data_validation_errors(self, tmp_path, caplog):
        site = factories.SiteFactory.create()
        data = [
            f"invalid_id,2023-02-02 21:21:10.713,testuser@test.com,2023-02-02 21:21:39.864,testuser@test.com,"
            f"Test Gallery 1,Description 1,Published,{site.id},,,"
        ]
        table = self.build_table(data)
        filepath = tmp_path / "gallery.csv"
        with open(filepath, "w") as file:
            file.write(table.export("csv"))
        call_command("import_gallery_data", filepath=tmp_path)

        assert Gallery.objects.filter(site=site).count() == 0
        assert GalleryItem.objects.count() == 0

        assert (
            "Validation errors encountered while importing gallery.csv:" in caplog.text
        )
        assert (
            "Row 0: Field Errors: {}, Non-Field Errors: ['“invalid_id” is not a valid UUID.']"
            in caplog.text
        )
        assert "Gallery import completed." in caplog.text

    @pytest.mark.django_db
    def test_import_gallery_data_exception(self, tmp_path, caplog):
        site = factories.SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,testuser@test.com,2023-02-02 21:21:39.864,testuser@test.com,"
            f"Test Gallery 1,Description 1,Published,{site.id},,,"
        ]
        table = self.build_table(data)
        filepath = tmp_path / "gallery.csv"
        with open(filepath, "w") as file:
            file.write(table.export("csv"))
            with patch(
                "backend.resources.gallery.GalleryResource.import_data",
                side_effect=Exception("Mocked exception"),
            ):
                call_command("import_gallery_data", filepath=tmp_path)

        assert "Error processing file gallery.csv: " in caplog.text
