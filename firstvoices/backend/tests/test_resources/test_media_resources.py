import uuid

import pytest
import tablib

from backend.models.media import Person
from backend.resources.media import PersonResource
from backend.tests.factories import SiteFactory


class TestPersonImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "id,created,created_by,last_modified,last_modified_by,name,bio,site",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Person object with basic fields"""
        site = SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2019-05-08 12:11:02.372,user_one@test.com,2019-12-19 09:23:07.303,user_two@test.com,Clifford,Yes it's Clifford the Big Red Dog.,{site.id}",  # noqa E501
            f"{uuid.uuid4()},2020-05-23 03:48:21.202,user_one@test.com,2023-01-24 15:27:43.969,user_two@test.com,My Favorite Person,,{site.id}",  # noqa E501
        ]
        table = self.build_table(data)

        result = PersonResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Person.objects.filter(site=site.id).count() == len(data)

        new_person = Person.objects.get(id=table["id"][0])
        assert table["name"][0] == new_person.name
        assert table["site"][0] == str(new_person.site.id)
        assert table["bio"][0] == new_person.bio
